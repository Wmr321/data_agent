from langgraph.runtime import Runtime
from datetime import date

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger

async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外信息", "status": "running"})
    logger.info("开始添加额外信息")

    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]

        # 当前的时间信息
        today = date.today()
        # 日期
        _date = today.strftime("%Y-%m-%d")
        # 星期
        weekday = today.strftime("%A")
        # 季度
        quarter = f"Q{(today.month - 1) // 3 + 1}"

        date_info = DateInfoState(date=_date, weekday=weekday, quarter=quarter)

        # 数据仓库环境信息
        db_info = await dw_mysql_repository.get_db_info()

        db_info_state: DBInfoState = DBInfoState(**db_info)

        writer({"type": "progress", "step": "添加额外信息", "status": "success"})
        logger.info(f"额外上下文信息：数据库信息-{db_info_state} 日期信息-{date_info}")

        return {"date_info": date_info, "db_info": db_info_state}

    except Exception as e:
        writer({"type": "progress", "step": "添加额外信息", "status": "error"})
        logger.info("添加额外信息失败")

        raise e
