from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.agent.api.dependencies import get_query_service
from app.agent.api.scheme.query_scheme import QueryScheme
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.post("/api/query")
async def query(
    _query: QueryScheme, query_service: QueryService = Depends(get_query_service)
):
    return StreamingResponse(
        query_service.query(_query.query), media_type="text/event-stream"
    )
