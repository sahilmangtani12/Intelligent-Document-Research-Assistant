from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DocumentStatus = Literal["processing", "ready", "failed"]


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: Literal["pdf", "txt", "csv"]
    size_bytes: int
    status: DocumentStatus
    error: str | None = None
    chunk_count: int
    unit_count: int  # pages (PDF), rows (CSV), 1 (TXT)
    created_at: datetime


class ChunkOut(BaseModel):
    chunk_id: str
    text: str
    page: int | None = None
    row: int | None = None
    location: str


class DocumentSourcesOut(BaseModel):
    document_id: str
    filename: str
    total_chunks: int
    chunks: list[ChunkOut]


class StatsOut(BaseModel):
    documents_total: int
    documents_ready: int
    documents_processing: int
    documents_failed: int
    total_chunks: int
    by_type: dict[str, int]
    queries_total: int
    queries_answered: int
    queries_unanswered: int
    avg_latency_ms: int
    supported_types: list[str]
    max_upload_mb: int
