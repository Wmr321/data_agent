from dataclasses import dataclass


@dataclass
class MetricInfo:
    id: str
    name: str | None
    description: str | None
    relevant_columns: dict | list | None
    alias: dict | list | None