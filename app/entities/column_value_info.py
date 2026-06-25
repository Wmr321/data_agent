from dataclasses import dataclass


@dataclass
class ColumnValueInfo:
    id: str
    column_value: str
    column_id: str