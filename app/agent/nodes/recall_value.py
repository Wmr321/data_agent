from langchain_core.output_parsers import JsonOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.clients.llm import text_model
from app.entities.column_value_info import ColumnValueInfo
from app.prompts_load.prompts_load import my_prompt_load
from app.core.log import logger

async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})
    logger.info("开始召回字段取值")

    try:
        query = state["query"]
        keywords = state["keywords"]
        column_value_es_repository = runtime.context['column_value_es_repository']

        # 使用LLM扩展关键词
        template = my_prompt_load(name="extend_keywords_for_value_recall.yaml")
        output_parser = JsonOutputParser()
        chain = template | text_model | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)
        logger.info(f"为召回相关字段取值，扩充的关键词为：{keywords}")

        # 全文检索相关字段取值
        column_value_infos: list[ColumnValueInfo] = []
        for keyword in keywords:
            column_value_infos.extend(await column_value_es_repository.search(keyword, score_stand=0.6, limit=20))
        column_value_infos_dict: dict[str, ColumnValueInfo] = {}
        for column_value_info in column_value_infos:
            if column_value_info.id not in column_value_infos_dict:
                column_value_infos_dict[column_value_info.id] = column_value_info

        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"召回的相关字段取值为：{list(column_value_infos_dict.keys())}")

        return {"column_value_infos": list(column_value_infos_dict.values())}
    except Exception as e:
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        logger.info(f"召回相关字段取值失败")

        raise e