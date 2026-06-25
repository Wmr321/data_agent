from dataclasses import asdict

from app.entities.column_metric import ColumnMetric
from app.models.column_metric_mysql import ColumnMetricMysql


class ColumnMetricMapper:
    @staticmethod
    def to_entity(column_metric: ColumnMetricMysql):
        return ColumnMetric(
            column_id = column_metric.column_id,
            metric_id = column_metric.metric_id
        )
    @staticmethod
    def to_model(column_metric: ColumnMetric):
        return ColumnMetricMysql(**asdict(column_metric))