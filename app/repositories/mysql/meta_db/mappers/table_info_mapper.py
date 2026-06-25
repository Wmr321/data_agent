from dataclasses import asdict

from app.entities.table_info import TableInfo
from app.models.table_info_mysql import TableInfoMysql


class TableInfoMapper:
    @staticmethod
    def to_entity(table: TableInfoMysql):
        return TableInfo(
            id = table.id,
            name = table.name,
            role = table.role,
            description = table.description
        )
    @staticmethod
    def to_model(table: TableInfo):
        return TableInfoMysql(**asdict(table))