from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.conf.app_config import EmbeddingConfig, app_config

class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: HuggingFaceEndpointEmbeddings | None = None
        self.config = config

    def init(self):
        self.client = HuggingFaceEndpointEmbeddings(model= f"http://{self.config.host}:{self.config.port}")


embedding_client_manager = EmbeddingClientManager(app_config.embedding)
