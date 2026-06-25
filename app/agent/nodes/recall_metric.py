from langchain_core.output_parsers import JsonOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.clients.llm import text_model
from app.entities.metric_info import MetricInfo
from app.prompts_load.prompts_load import my_prompt_load
from app.core.log import logger

async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标信息", "status": "running"})
    logger.info("开始召回指标信息")

    try:
        query = state["query"]
        keywords = state["keywords"]
        embedding_client = runtime.context['embedding_client']
        metric_qdrant_repository = runtime.context['metric_qdrant_repository']

        # 使用LLM扩展关键词
        template = my_prompt_load(name="extend_keywords_for_metric_recall.yaml")
        output_parser = JsonOutputParser()
        chain = template | text_model | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)
        logger.info(f"为召回相关指标信息，扩充的关键词为：{keywords}")

        # 向量检索相关字段
        metric_infos: list[MetricInfo] = []
        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            metric_infos.extend(await metric_qdrant_repository.search(embedding, score_stand=0.6, limit=20))
        metric_infos_dict: dict[str, MetricInfo] = {}
        for metric_info in metric_infos:
            if metric_info.id not in metric_infos_dict:
                metric_infos_dict[metric_info.id] = metric_info
        writer({"type": "progress", "step": "召回指标信息", "status": "success"})
        logger.info(f"检索到相关指标为：{list(metric_infos_dict.keys())}")
        return {"metric_infos": list(metric_infos_dict.values())}
    except Exception as e:
        writer({"type": "progress", "step": "召回指标信息", "status": "error"})
        logger.info(f"检索相关指标信息失败")

        raise e

