from dataclasses import asdict

from elasticsearch import AsyncElasticsearch

from app.entities.column_value_info import ColumnValueInfo


class ColumnValueEsRepository:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client
        self.column_value_index = 'column_value_index'
        self.mappings = {
            'dynamic': False,
            'properties':{
                'id':{'type': 'keyword'},
                'column_value':{'type': 'text', 'analyzer': 'ik_max_word', 'search_analyzer': 'ik_max_word'},
                'column_id':{'type': 'keyword'}
            }
        }
    async def ensure_index(self):
        if not await self.client.indices.exists(index= self.column_value_index):
            await self.client.indices.create(
                index= self.column_value_index,
                mappings= self.mappings
            )

    async def index(self, column_value_infos: list[ColumnValueInfo], batch_size: int= 10):
        for i in range(0, len(column_value_infos), batch_size):
            batch_column_value_infos = column_value_infos[i: i+batch_size]
            operations = []
            for column_value in batch_column_value_infos:
                operations.append({
                    "index":{
                        "_index": self.column_value_index
                    }
                })
                operations.append(asdict(column_value))
            await self.client.bulk(operations= operations)

    async def search(self, keyword: str, score_stand: float = 0.6, limit: int = 20):
        result = await self.client.search(
            index=self.column_value_index,
            query={
                "match": {
                    "column_value": {
                        "query": keyword
                    }
                }
            },
            size=limit,
            min_score=score_stand
        )
        return [ColumnValueInfo(**hit["_source"]) for hit in result["hits"]["hits"]]
