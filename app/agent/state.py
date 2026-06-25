from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.column_value_info import ColumnValueInfo
from app.entities.metric_info import MetricInfo

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]

class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]

class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str

class DBInfoState(TypedDict):
    dialect: str
    version: str

class DataAgentState(TypedDict):
    query: str

    keywords: list
    column_infos: list[ColumnInfo]
    metric_infos: list[MetricInfo]
    column_value_infos: list[ColumnValueInfo]

    table_infos: list[TableInfoState]  # 表信息
    final_metric_infos: list[MetricInfoState]  # 指标信息

    date_info: DateInfoState
    db_info: DBInfoState

    sql: str

    error: str