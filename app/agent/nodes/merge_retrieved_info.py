from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState, MetricInfoState
from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo
from app.core.log import logger

async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})
    logger.info("开始合并召回信息")

    try:
        # 已召回信息
        column_infos = state["column_infos"]
        metric_infos = state["metric_infos"]
        column_value_infos = state["column_value_infos"]

        # 获取所需依赖
        meta_mysql_repository = runtime.context["meta_mysql_repository"]

        #用于去重
        columns_map: dict[str, ColumnInfo] = {column_info.id: column_info for column_info in column_infos}

        # 合并表格信息
        table_infos: list[TableInfoState] = []

        # 将指标信息的相关字段加入字段信息列表
        for metric_info in metric_infos:
            relevant_columns = metric_info.relevant_columns
            for relevant_column in relevant_columns:
                if relevant_column not in columns_map:
                    column_info = await meta_mysql_repository.get_column_info_by_id(relevant_column)
                    columns_map[relevant_column] = column_info


        # 将字段取值合并到字段信息列表
        for column_value_info in column_value_infos:
            column_value = column_value_info.column_value
            column_id = column_value_info.column_id

            if column_id not in columns_map:
                column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                columns_map[column_id] = column_info
            if column_value not in columns_map[column_id].examples:
                columns_map[column_id].examples.append(column_value)


        # 按照字段所属的表id进行分组，得到table_id->columns映射
        table_to_columns_map: dict[str, list[ColumnInfo]] = {}

        for column in columns_map.values():
            table_id = column.table_id
            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []
            table_to_columns_map[table_id].append(column)

        # 显式的添加每个表的主外键
        for table_id in table_to_columns_map.keys():
            # 查询主外键字段
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)

            # 当前表已有的所有列的ID
            column_ids = [column.id for column in table_to_columns_map[table_id]]

            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_to_columns_map[table_id].append(key_column)

        # 将table_id->columns映射 转换为 list[TableInfoState]
        for table_id, columns in table_to_columns_map.items():
            table: TableInfo = await  meta_mysql_repository.get_table_info_by_id(table_id)
            columns = [
                ColumnInfoState(name=column.name, type=column.type, role=column.role, examples=column.examples,
                                description=column.description, alias=column.alias)
                for column in columns]
            table_info_state = TableInfoState(name=table.name,
                                              role=table.role,
                                              description=table.description,
                                              columns=columns)
            table_infos.append(table_info_state)

        # 处理指标信息
        final_metric_infos: list[MetricInfoState] = [
            MetricInfoState(name=metric_info.name, description=metric_info.description,
                            relevant_columns=metric_info.relevant_columns, alias=metric_info.alias)
            for metric_info in metric_infos]

        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(
            f"合并召回信息: "
            f"表信息-{[table_info['name'] for table_info in table_infos]}"
            f"指标信息-{[final_metric_info['name'] for final_metric_info in final_metric_infos]}")
        logger.info(f"字段信息：{columns_map.keys()}")

        return {"table_infos": table_infos, "final_metric_infos": final_metric_infos}

    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.info("合并召回信息失败")

        raise e