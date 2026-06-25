from elasticsearch import AsyncElasticsearch
from app.conf.app_config import EsConfig, app_config


class EsClientManager:
    def __init__(self, config: EsConfig):
        self.client: AsyncElasticsearch | None = None
        self.config: EsConfig = config

    def init(self):
        self.client = AsyncElasticsearch(
            hosts= [f"http://{self.config.host}:{self.config.port}"]
        )
    async def close(self):
        await self.client.close()

es_client_manager = EsClientManager(app_config.es)