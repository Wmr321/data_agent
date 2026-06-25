import yaml
from langchain_core.output_parsers import StrOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.clients.llm import code_model
from app.prompts_load.prompts_load import my_prompt_load
from app.core.log import logger

async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校正sql", "status": "running"})
    logger.info("开始校正sql")

    try:
        sql = state["sql"]
        error = state["error"]

        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]

        prompt = my_prompt_load(name="correct_sql.yaml")
        output_parser = StrOutputParser()
        chain = prompt | code_model | output_parser

        result = await chain.ainvoke(
            {"query": query,
             "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
             "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
             "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
             "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
             "sql": sql,
             "error": error
             })


        writer({"type": "progress", "step": "校正sql", "status": "success"})
        logger.info(f"校正后的SQL: {result}")

        return {"sql": result}

    except Exception as e:
        writer({"type": "progress", "step": "校正sql", "status": "error"})
        logger.info("校正sql失败")

        raise e


