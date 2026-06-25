from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:
    def __init__(self, qdrant_client: AsyncQdrantClient):
        self.client = qdrant_client
        self.collection = "column_info_collection"
    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection):
            await self.client.create_collection(
                collection_name= self.collection,
                vectors_config= VectorParams(size= app_config.qdrant.embedding_size, distance= Distance.COSINE)
            )

    async def upsert(self, ids: list[str],
                     embeddings: list[list[float]], payloads: list[dict], batch_size: int = 10):
        points: list[PointStruct] = [PointStruct(id= id, vector= embedding, payload= payload)
                                     for id, embedding, payload in zip(ids, embeddings, payloads)]
        for i in range(0, len(points), batch_size):
            batch_points = points[i: i+batch_size]
            await self.client.upsert(collection_name= self.collection, points= batch_points)

    async def search(self, embedding: list[float], score_stand: float = 0.6, limit: int = 20):
        result = await self.client.query_points(
            collection_name=self.collection,
            query=embedding,
            limit=limit,
            score_threshold=score_stand
        )
        return [ColumnInfo(**point.payload) for point in result.points]
