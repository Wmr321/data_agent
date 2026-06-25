import yaml
from langchain_core.output_parsers import JsonOutputParser
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.clients.llm import text_model
from app.core.log import logger
from app.prompts_load.prompts_load import my_prompt_load


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标信息", "status": "running"})
    logger.info("开始过滤指标信息")

    try:
        query = state["query"]
        metric_infos = state["final_metric_infos"]

        # 用LLM过滤表信息
        template = my_prompt_load(name="filter_metric_info.yaml")
        output_parser = JsonOutputParser()

        chain = template | text_model | output_parser

        result = await chain.ainvoke(
            {"query": query, "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)})

        # 利用模型输出过滤metric_infos
        filter_metric_info = [metric_info for metric_info in metric_infos if metric_info["name"] in result]

        writer({"type": "progress", "step": "过滤指标信息", "status": "success"})
        logger.info(f"过滤后的指标: {[metric_info['name'] for metric_info in filter_metric_info]}")
        return {"metric_infos": filter_metric_info}

    except Exception as e:
        writer({"type": "progress", "step": "过滤指标信息", "status": "error"})
        logger.info("过滤指标信息失败")

        raise e


