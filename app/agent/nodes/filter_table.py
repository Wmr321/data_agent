import yaml
from langchain_core.output_parsers import JsonOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState
from app.clients.llm import text_model
from app.prompts_load.prompts_load import my_prompt_load
from app.core.log import logger

async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表格信息", "status": "running"})
    logger.info("开始过滤表格信息")

    try:
        query = state["query"]
        table_infos = state["table_infos"]

        # 用LLM过滤表信息
        template = my_prompt_load("filter_table_info.yaml")
        output_parser = JsonOutputParser()

        chain = template | text_model | output_parser

        result = await chain.ainvoke(
            {"query": query, "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False)})

        filter_table_infos: list[TableInfoState] = []
        for table_info in table_infos:
            if table_info["name"] in result:
                table_info["columns"] = [column for column in table_info["columns"]
                                         if column["name"] in result[table_info["name"]]]
                filter_table_infos.append(table_info)

        writer({"type": "progress", "step": "过滤表格信息", "status": "success"})
        logger.info(f"过滤后的表信息: {[table_info['name'] for table_info in filter_table_infos]}")

        return {"table_infos": filter_table_infos}

    except Exception as e:
        writer({"type": "progress", "step": "过滤表格信息", "status": "error"})
        logger.info(f"过滤表信息失败")

        raise e

