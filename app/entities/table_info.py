from dataclasses import dataclass


@dataclass
class TableInfo:
    id: str
    name: str | None
    role: str | None
    description: str | None