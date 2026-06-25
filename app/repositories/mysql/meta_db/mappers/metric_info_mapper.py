from dataclasses import asdict

from app.entities.metric_info import MetricInfo
from app.models.metric_info_mysql import MetricInfoMysql

class MetricInfoMapper:
    @staticmethod
    def to_entity(metric: MetricInfoMysql):
        return MetricInfo(
            id = metric.id,
            name = metric.name,
            description = metric.description,
            relevant_columns = metric.relevant_columns,
            alias = metric.alias
        )
    @staticmethod
    def to_model(metric: MetricInfo):
        return MetricInfoMysql(**asdict(metric))