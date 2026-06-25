import json
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.repositories.es.column_value_es_repository import ColumnValueEsRepository
from app.repositories.mysql.dw_db.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_db.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(
            self,
            column_qdrant_repository: ColumnQdrantRepository,
            embedding_client: HuggingFaceEndpointEmbeddings,
            metric_qdrant_repository: MetricQdrantRepository,
            column_value_es_repository: ColumnValueEsRepository,
            meta_mysql_repository: MetaMysqlRepository,
            dw_mysql_repository: DwMysqlRepository
        ):
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.metric_qdrant_repository = metric_qdrant_repository
        self.column_value_es_repository = column_value_es_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
    async def query(self, _query: str):
        state = DataAgentState(query=_query)
        context = DataAgentContext(
            column_qdrant_repository=self.column_qdrant_repository,
            embedding_client=self.embedding_client,
            metric_qdrant_repository=self.metric_qdrant_repository,
            column_value_es_repository=self.column_value_es_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository
        )

        try:
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"

        except Exception as e:
            error = {"type": "error", "message": f"{str(e)}"}
            yield f"data: {json.dumps(error, ensure_ascii=False, default=str)}\n\n"
