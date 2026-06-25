from dataclasses import asdict

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.models.column_info_mysql import ColumnInfoMysql
from app.models.column_metric_mysql import ColumnMetricMysql


class ColumnInfoMapper:
    @staticmethod
    def to_entity(column: ColumnInfoMysql):
        return ColumnInfo(
            id = column.id,
            name = column.name,
            type = column.type,
            role = column.role,
            examples = column.examples,
            description = column.description,
            alias = column.alias,
            table_id = column.table_id,
        )
    @staticmethod
    def to_model(column: ColumnInfo):
        return ColumnInfoMysql(**asdict(column))