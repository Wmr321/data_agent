import uuid
from dataclasses import asdict
from pathlib import Path
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.core.log import logger
from app.conf.meta_config import MetaConfig

from app.entities.column_info import ColumnInfo
from app.entities.column_value_info import ColumnValueInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo

from app.repositories.es.column_value_es_repository import ColumnValueEsRepository
from app.repositories.mysql.dw_db.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_db.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaDBService:
    def __init__(self, meta_mysql_repository: MetaMysqlRepository,
                 dw_mysql_repository: DwMysqlRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 column_value_es_repository: ColumnValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository
                 ):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.column_value_es_repository = column_value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def _build_meta_table_and_column(self, meta_config: MetaConfig) -> list[ColumnInfo]:
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        for table in meta_config.tables:
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            )
            table_infos.append(table_info)
            column_types = await self.dw_mysql_repository.get_column_types(table.name)
            for column in table.columns:
                column_values = await self.dw_mysql_repository.get_column_values(table.name, column.name)
                column_info = ColumnInfo(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name,
                )
                column_infos.append(column_info)
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos



    async def _build_meta_metric_and_metric_column(self, meta_config: MetaConfig) -> list[MetricInfo]:
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []
        for metric in meta_config.metrics:
            # 构造MetricInfo数据
            metric_info = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
            )
            metric_infos.append(metric_info)

            for relevant_column in metric.relevant_columns:
                # 构造ColumnMetric数据
                column_metric = ColumnMetric(
                    column_id=relevant_column, metric_id=metric.name
                )
                column_metrics.append(column_metric)
        # 保存到元数据数据库
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_infos(metric_infos)
            await self.meta_mysql_repository.save_column_metrics(column_metrics)
        return metric_infos

    async def _build_meta_column_qdrant_index(self, column_infos: list[ColumnInfo]):
        await self.column_qdrant_repository.ensure_collection()
        points = []
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_txt": column_info.name,
                "payload": asdict(column_info)
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_txt": column_info.description,
                "payload": asdict(column_info)
            })
            for alia in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_txt": alia,
                    "payload": asdict(column_info)
                })
        embeddings: list[list[float]] = []
        embedding_texts = [point["embedding_txt"] for point in points]
        embedding_batch_size = 20
        for i in range(0, len(embedding_texts), embedding_batch_size):
            batch_embedding_texts = embedding_texts[i: i + embedding_batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
            embeddings.extend(batch_embeddings)
        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)


    async def _build_meta_metric_qdrant_index(self, metric_infos: list[MetricInfo]):
        await self.metric_qdrant_repository.ensure_collection()
        points = []
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_txt": metric_info.name,
                "payload": asdict(metric_info)
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_txt": metric_info.description,
                "payload": asdict(metric_info)
            })
            for alia in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_txt": alia,
                    "payload": asdict(metric_info)
                })
        embeddings: list[list[float]] = []
        embedding_texts = [point["embedding_txt"] for point in points]
        embedding_batch_size = 20
        for i in range(0, len(embedding_texts), embedding_batch_size):
            batch_embedding_texts = embedding_texts[i: i + embedding_batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
            embeddings.extend(batch_embeddings)
        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)

    async def _build_dw_column_es_index(self, meta_config: MetaConfig):
        await self.column_value_es_repository.ensure_index()
        column_value_infos: list[ColumnValueInfo] = []
        for table in meta_config.tables:
            for column in table.columns:
                if column.sync:
                    values = await self.dw_mysql_repository.get_column_values(table_name=table.name,
                                                                              column_name=column.name,
                                                                              limit=1000000)
                    for value in values:
                        column_value_infos.append(ColumnValueInfo(id=f"{table.name}.{column.name}.{value}",
                                                                  column_value=value,
                                                                  column_id=f"{table.name}.{column.name}"))
        await self.column_value_es_repository.index(column_value_infos=column_value_infos, batch_size=10)

    async def build(self, config_path: Path):
        logger.info("加载元数据库配置信息....")
        meta_config_content = OmegaConf.load(config_path)
        meta_config_schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(meta_config_schema, meta_config_content))
        logger.info("元数据库配置文件加载成功")

        if meta_config.tables:
            ##构建table_info和column_info
            logger.info("开始构建元数据库中的table_info和column_info")
            column_infos = await self._build_meta_table_and_column(meta_config)
            logger.info("元数据库中的table_info和column_info构建成功")

            ##构建column_info表的name、description、alias三个字段的向量索引
            logger.info("开始构建column_info的向量索引")
            await self._build_meta_column_qdrant_index(column_infos)
            logger.info("column_info的向量索引构建成功")

            ##建立字段取值的全文索引
            logger.info("开始构建数据仓库中维度字段的全文索引")
            await self._build_dw_column_es_index(meta_config)
            logger.info("数据仓库的全文索引构建成功")
        if meta_config.metrics:
            ##构建metric_info和metric_column
            logger.info("开始构建元数据库中的metric_info和metric_column")
            metric_infos = await self._build_meta_metric_and_metric_column(meta_config)
            logger.info("元数据库中的metric_info和metric_column构建成功")

            ##构建metric_info表的name、description、alias三个字段的向量索引
            logger.info("开始构建metric_info的向量索引")
            await self._build_meta_metric_qdrant_index(metric_infos)
            logger.info("metric_info的向量索引构建成功")










