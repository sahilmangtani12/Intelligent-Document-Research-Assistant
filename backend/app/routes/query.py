from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query_documents(body: QueryRequest, c: Container = Depends(get_container)):
    response = c.pipeline.answer(body.question, top_k=body.top_k, document_ids=body.document_ids)
    c.db.record_query(response.grounded, response.latency_ms)
    return response
