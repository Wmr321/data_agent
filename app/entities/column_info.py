from dataclasses import dataclass


@dataclass
class ColumnInfo:
    id: str
    name: str | None
    type: str | None
    role: str | None
    examples: dict | list | None
    description: str | None
    alias: dict | list | None
    table_id: str | None