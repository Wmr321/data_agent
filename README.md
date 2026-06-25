# DataAgent — 自然语言查询数据仓库系统

让业务人员用**自然语言**（中文）直接查询数据仓库，无需编写 SQL。

## 核心能力

- 输入中文自然语言 → 自动生成 SQL → 在数据仓库执行 → 返回结果
- 多轮语义召回（向量检索 + 全文检索）自动定位相关字段、指标和取值
- SQL 自动校验与自纠错（validate → correct → execute 闭环）
- SSE 流式推送每步执行进度，前端实时可见

## 架构总览

```
用户查询（中文自然语言）
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                     Agent 管道 (LangGraph)               │
│                                                         │
│ ① extract_keywords     ── jieba 关键词抽取              │
│       │                 (毫秒级，过滤无意义词性)          │
│       ├──────────────────────┬──────────────────┐       │
│       ▼                      ▼                  ▼       │
│ ② recall_column    ③ recall_metric   ④ recall_value     │
│    Qdrant 向量检索    Qdrant 向量检索    ES 全文检索      │
│    (LLM 扩词+语义匹配) (LLM 扩词+语义匹配) (IK分词+倒排) │
│       │                      │                  │       │
│       └──────────┬───────────┴────────┬─────────┘       │
│                  ▼                    ▼                  │
│         ⑤ merge_retrieved_info                          │
│          去重、补全主外键、组装成表结构                    │
│                  │                                       │
│         ⑥ filter_table  +  ⑦ filter_metric              │
│           LLM 过滤无关表/列     LLM 过滤无关指标           │
│                  │                                       │
│         ⑧ add_extra_context                              │
│           当前日期 + 数据库方言                            │
│                  │                                       │
│         ⑨ generate_sql    (qwen3-coder)                  │
│                  │                                       │
│         ⑩ validate_sql         ──── 正确 ──→ ⑫ execute │
│                  │                        │              │
│             错误  │◄── ⑪ correct_sql ──────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    SSE 流式响应：进度 + 查询结果
```

## 技术栈

| 组件 | 用途 |
|------|------|
| **FastAPI** | Web 服务框架，提供 REST API + SSE 流式响应 |
| **LangGraph** | Agent 管道编排（有状态 DAG，11 个节点） |
| **Qdrant** | 向量数据库，字段/指标的语义向量检索 |
| **Elasticsearch** | 全文检索引擎（IK 中文分词），字段取值精确匹配 |
| **MySQL × 2** | `meta` 库存元数据（表结构、字段定义、指标定义）；`dw` 库为真实数据仓库 |
| **Text Embeddings Inference** | 部署 BAAI/bge-large-zh-v1.5 中文 Embedding 模型 |
| **LLM（通义千问）** | `qwen3-max` 用于文本理解（扩词/过滤），`qwen3-coder-next` 用于 SQL 生成与修正 |
| **jieba** | TF-IDF 中文关键词抽取（第一道过滤器） |
| **Docker Compose** | 一键编排所有中间件服务 |

## 快速开始

### 前置要求

- Docker & Docker Compose
- 至少 8 GB 可用内存（推荐 16 GB）
- 通义千问 API Key（[DashScope](https://help.aliyun.com/zh/model-studio/)）

### 1. 下载 Embedding 模型

```bash
# 创建模型目录
mkdir -p docker/embedding

# 下载 bge-large-zh-v1.5（约 1.3 GB）
# 方式一：从 HuggingFace 下载
git lfs install
git clone https://huggingface.co/BAAI/bge-large-zh-v1.5 docker/embedding/bge-large-zh-v1.5

# 方式二：从 ModelScope 下载（国内推荐）
# git clone https://www.modelscope.cn/BAAI/bge-large-zh-v1.5.git docker/embedding/bge-large-zh-v1.5
```

### 2. 配置

```bash
# 编辑应用配置，填入你的 API Key
vim conf/app_config.yaml

# 关键配置项
llm:
  api_key: sk-xxxxxx                          # 你的 DashScope API Key
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  text_model: qwen3-max
  code_model: qwen3-coder-next
```

### 3. 启动所有服务

```bash
docker compose -f docker/docker-compose.yaml up -d
```

这会启动：
- MySQL（`:3306`）— 元数据库 + 数据仓库
- Elasticsearch（`:9200`）+ Kibana（`:5601`）
- Qdrant（`:6333`）— 向量数据库
- TEI（`:8081`）— Embedding 推理服务

### 4. 构建元数据索引

```bash
# 将表结构、字段、指标信息写入 MySQL + Qdrant + ES
uv run python app/scripts/build_meta_db.py -c conf/meta_config.yaml
```

### 5. 启动 API 服务

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 查询示例

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "查询李伟买了哪些产品，在哪里买的，总共花了多少钱"}'
```

SSE 流式响应：

```
data: {"type": "progress", "step": "抽取关键词", "status": "running"}
data: {"type": "progress", "step": "抽取关键词", "status": "success"}
data: {"type": "progress", "step": "召回字段信息", "status": "running"}
...
data: {"type": "progress", "step": "生成sql", "status": "success"}
data: {"type": "progress", "step": "校验sql", "status": "success"}
data: {"type": "progress", "step": "执行sql", "status": "success"}
data: {"type": "result", "data": [{"product_name": "...", "region_name": "...", "order_amount": ...}]}
```

## 项目结构

```
├── main.py                          # FastAPI 应用入口
├── conf/
│   ├── app_config.yaml              # 应用配置（数据库/ES/Qdrant/LLM）
│   └── meta_config.yaml             # 元数据定义（表结构、指标、同义词）
├── prompts/                         # LLM Prompt 模板
│   ├── generate_sql.yaml
│   ├── correct_sql.yaml
│   ├── filter_table_info.yaml
│   ├── filter_metric_info.yaml
│   ├── extend_keywords_for_column_recall.yaml
│   ├── extend_keywords_for_metric_recall.yaml
│   └── extend_keywords_for_value_recall.yaml
├── app/
│   ├── agent/                       # LangGraph Agent 管道
│   │   ├── graph.py                 # DAG 定义（11 个节点 + 条件边）
│   │   ├── state.py                 # 状态定义
│   │   ├── context.py               # 上下文（各类 Repository）
│   │   ├── nodes/                   # 各节点实现
│   │   │   ├── extract_keywords.py       # ① 关键词抽取
│   │   │   ├── recall_column.py          # ② 字段召回（Qdrant）
│   │   │   ├── recall_metric.py          # ③ 指标召回（Qdrant）
│   │   │   ├── recall_value.py           # ④ 取值召回（ES）
│   │   │   ├── merge_retrieved_info.py   # ⑤ 合并信息
│   │   │   ├── filter_table.py           # ⑥ 过滤表
│   │   │   ├── filter_metric.py          # ⑦ 过滤指标
│   │   │   ├── add_extra_context.py      # ⑧ 补充上下文
│   │   │   ├── generate_sql.py           # ⑨ 生成 SQL
│   │   │   ├── validate_sql.py           # ⑩ 校验 SQL
│   │   │   ├── correct_sql.py            # ⑪ 修正 SQL
│   │   │   └── execute_sql.py            # ⑫ 执行 SQL
│   │   └── api/                      # FastAPI API 层
│   │       ├── lifespan.py             # 启动/停止生命周期
│   │       ├── dependencies.py         # 依赖注入
│   │       └── routers/query_router.py # POST /api/query
│   ├── clients/                      # 外部客户端管理
│   │   ├── llm.py                    # LLM 模型初始化
│   │   ├── qdrant_client_manager.py
│   │   ├── es_client_manager.py
│   │   ├── mysql_client_manager.py
│   │   └── embedding_client_manager.py
│   ├── repositories/                 # 数据访问层
│   │   ├── qdrant/                   # Qdrant 向量检索
│   │   ├── es/                       # ES 全文检索
│   │   └── mysql/                    # MySQL（meta + dw）
│   ├── services/
│   │   ├── query_service.py          # 查询服务（编排 Agent）
│   │   └── meta_db_service.py        # 元数据构建服务
│   ├── entities/                     # 数据实体定义
│   ├── models/                       # SQLAlchemy ORM 模型
│   ├── conf/                         # 配置加载
│   ├── core/                         # 基础设施（日志、上下文）
│   └── prompts_load/                 # Prompt 加载器
├── docker/
│   └── docker-compose.yaml           # 中间件编排
└── pyproject.toml                    # Python 依赖
```

## 元数据配置

在 `conf/meta_config.yaml` 中定义数据仓库的表结构、字段和指标：

```yaml
tables:
  - name: dim_customer
    role: dim                     # dim = 维度表, fact = 事实表
    description: 客户维度表
    columns:
      - name: customer_name
        role: dimension
        description: 客户名称
        alias: [客户名称, 用户名称]   # 同义词，用于向量召回
        sync: true                  # 是否同步字段取值到 ES 全文索引

metrics:
  - name: GMV
    description: 成交金额总和
    relevant_columns:
      - fact_order.order_amount
    alias: [成交总额, 订单总额]
```

## 核心设计

### 双检索架构

| 检索方式 | 引擎 | 召回对象 | 匹配方式 |
|---------|------|---------|---------|
| 向量检索 | Qdrant | 字段名/字段描述/指标/同义词 | 语义相似（cosine） |
| 全文检索 | ES + IK | 维度字段具体取值（人名/地名等） | 精确分词匹配（BM25） |

> **为什么用两个？** Qdrant 解决"成交总额"→`order_amount` 的语义鸿沟；ES 解决"李伟"→`customer_name='李伟'` 的精确匹配——两者互补，缺一不可。

### SQL 自纠错闭环

```
生成 SQL → EXPLAIN 校验 → 通过 → 执行
                    ↓ 失败
               LLM 根据错误信息修正 → 重新校验 → 执行
```

## 环境要求

- Python ≥ 3.12
- Docker & Docker Compose
- 推荐内存 ≥ 16 GB（ES + Qdrant + TEI 均需内存）

## License

MIT
