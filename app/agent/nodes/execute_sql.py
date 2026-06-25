from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行sql", "status": "running"})
    logger.info("开始执行sql")

    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        sql = state["sql"]

        result = await dw_mysql_repository.run_sql(sql)

        writer({"type": "progress", "step": "执行sql", "status": "success"})
        writer({"type": "result", "data": result})
        logger.info(f"执行结果为：{result}")

    except Exception as e:
        writer({"type": "progress", "step": "执行sql", "status": "error"})
        logger.info("执行sql失败")

        raise