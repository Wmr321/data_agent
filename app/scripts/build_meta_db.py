import argparse
import asyncio
from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager

from app.repositories.es.column_value_es_repository import ColumnValueEsRepository
from app.repositories.mysql.dw_db.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_db.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_db_service import MetaDBService


async def build(config_path: Path):
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()
    embedding_client_manager.init()
    async with (meta_mysql_client_manager.session_factory() as meta_session,
                dw_mysql_client_manager.session_factory() as dw_session
                ):
        meta_db_service = MetaDBService(meta_mysql_repository= MetaMysqlRepository(meta_session),
                                        dw_mysql_repository= DwMysqlRepository(dw_session),
                                        column_qdrant_repository= ColumnQdrantRepository(qdrant_client_manager.client),
                                        embedding_client= embedding_client_manager.client,
                                        column_value_es_repository= ColumnValueEsRepository(es_client_manager.client),
                                        metric_qdrant_repository= MetricQdrantRepository(qdrant_client_manager.client)
                                        )
        await meta_db_service.build(config_path)
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf')

    args = parser.parse_args()

    asyncio.run(build(Path(args.conf)))