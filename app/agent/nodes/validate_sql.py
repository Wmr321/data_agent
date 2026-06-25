from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校验sql", "status": "running"})
    logger.info("开始校验sql")

    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        sql = state["sql"]
        try:

            await dw_mysql_repository.validate_sql(sql)
            writer({"type": "progress", "step": "校验sql", "status": "success"})
            logger.info(f"SQL正确: {sql}")

            return {"error": None}

        except Exception as e:
            writer({"type": "progress", "step": "校验sql", "status": "success"})
            logger.error(f"SQL错误: {str(e)}")

            return {"error": str(e)}

    except Exception as e:
        writer({"type": "progress", "step": "校验sql", "status": "error"})
        logger.error(f"SQL校验失败: {str(e)}")

        raise e