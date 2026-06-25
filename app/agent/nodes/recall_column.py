from langchain_core.output_parsers import JsonOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.clients.llm import text_model
from app.entities.column_info import ColumnInfo
from app.prompts_load.prompts_load import my_prompt_load
from app.core.log import logger

async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段信息", "status": "running"})
    logger.info("开始召回字段信息")

    try:
        keywords = state["keywords"]
        query = state["query"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]
        embedding_client = runtime.context["embedding_client"]

        #扩充关键词，提高召回率
        template = my_prompt_load(name="extend_keywords_for_column_recall.yaml")
        output_parser = JsonOutputParser()
        chain = template | text_model | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)
        logger.info(f"为召回相关字段信息，扩充的关键词为：{keywords}")

        #向量检索相关字段
        column_infos: list[ColumnInfo] = []
        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            column_infos.extend(await column_qdrant_repository.search(embedding, score_stand=0.6, limit=20))
        column_infos_dict: dict[str, ColumnInfo] = {}
        for column_info in column_infos:
            if column_info.id not in column_infos_dict:
                column_infos_dict[column_info.id] = column_info

        writer({"type": "progress", "step": "召回字段信息", "status": "success"})
        logger.info(f"召回的相关字段为：{list(column_infos_dict.keys())}")

        return {"column_infos": list(column_infos_dict.values())}
    except Exception as e:
        writer({"type": "progress", "step": "召回字段信息", "status": "error"})
        logger.info(f"召回相关字段信息失败")

        raise e
