import logging
import uuid
from pathlib import Path

from app.config import Settings
from app.models.database import Database
from app.rag.chunking import Chunk, chunk_segments
from app.rag.loaders import load_document
from app.services.embedding_service import Embedder
from app.services.llm_service import location_label
from app.services.vector_store import VectorStore
from app.utils.errors import AppError, DocumentProcessingError, NotFoundError

log = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, db: Database, store: VectorStore, embedder: Embedder, settings: Settings):
        self._db, self._store, self._embedder, self._settings = db, store, embedder, settings

    def register(self, *, path: Path, filename: str, file_type: str, size_bytes: int) -> tuple[dict, list[Chunk]]:
        """Parse + chunk synchronously (fast; surfaces bad files immediately). Embedding happens later."""
        s = self._settings
        segments = load_document(path, file_type, max_csv_rows=s.max_csv_rows)
        chunks = chunk_segments(segments, file_type, chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
        if not chunks:
            raise DocumentProcessingError()
        if len(chunks) > s.max_chunks_per_document:
            raise DocumentProcessingError(
                f"This document produces {len(chunks):,} chunks; the limit is {s.max_chunks_per_document:,}."
            )
        unit_count = len({seg.metadata.get("page") for seg in segments}) if file_type == "pdf" else (
            len(segments) if file_type == "csv" else 1
        )
        record = self._db.create_document(
            id=uuid.uuid4().hex,
            filename=filename,
            file_type=file_type,
            size_bytes=size_bytes,
            unit_count=unit_count,
        )
        return record, chunks

    def index(self, document: dict, chunks: list[Chunk]) -> None:
        """Embed and store chunks. Runs as a background task; records success or failure."""
        doc_id = document["id"]
        try:
            embeddings = self._embedder.embed_documents([c.text for c in chunks])
            ids, metadatas = [], []
            for i, chunk in enumerate(chunks):
                ids.append(f"{doc_id}:{i}")
                meta = {
                    "document_id": doc_id,
                    "filename": document["filename"],
                    "file_type": document["file_type"],
                    "chunk_index": i,
                    "chunk_id": f"{doc_id}:{i}",
                    **chunk.metadata,
                }
                metadatas.append(meta)
            self._store.add_chunks(ids, embeddings, [c.text for c in chunks], metadatas)
            self._db.update_document(doc_id, status="ready", chunk_count=len(chunks), error=None)
        except Exception as exc:  # noqa: BLE001 - record any failure on the document
            log.exception("Indexing failed for %s", doc_id)
            message = exc.message if isinstance(exc, AppError) else "Indexing failed unexpectedly."
            try:
                self._store.delete_document(doc_id)  # no partial vectors left behind
            except Exception:  # noqa: BLE001
                pass
            self._db.update_document(doc_id, status="failed", error=message)

    def list(self) -> list[dict]:
        return self._db.list_documents()

    def get(self, doc_id: str) -> dict:
        doc = self._db.get_document(doc_id)
        if not doc:
            raise NotFoundError("Document not found.")
        return doc

    def delete(self, doc_id: str) -> None:
        self.get(doc_id)
        self._store.delete_document(doc_id)
        self._db.delete_document(doc_id)

    def chunks(self, doc_id: str, limit: int, offset: int) -> dict:
        doc = self.get(doc_id)
        items = self._store.get_document_chunks(doc_id, limit=limit, offset=offset)
        return {
            "document_id": doc_id,
            "filename": doc["filename"],
            "total_chunks": doc["chunk_count"],
            "chunks": [
                {
                    "chunk_id": i["chunk_id"],
                    "text": i["text"],
                    "page": i["metadata"].get("page"),
                    "row": i["metadata"].get("row"),
                    "location": location_label(i["metadata"]),
                }
                for i in items
            ],
        }

    def stats(self) -> dict:
        docs = self._db.list_documents()
        q = self._db.query_stats()
        by_type: dict[str, int] = {}
        for d in docs:
            by_type[d["file_type"]] = by_type.get(d["file_type"], 0) + 1
        count = lambda status: sum(1 for d in docs if d["status"] == status)  # noqa: E731
        return {
            "documents_total": len(docs),
            "documents_ready": count("ready"),
            "documents_processing": count("processing"),
            "documents_failed": count("failed"),
            "total_chunks": sum(d["chunk_count"] for d in docs),
            "by_type": by_type,
            "queries_total": q["total"],
            "queries_answered": q["answered"],
            "queries_unanswered": q["unanswered"],
            "avg_latency_ms": q["avg_latency_ms"],
            "supported_types": ["pdf", "txt", "csv"],
            "max_upload_mb": self._settings.max_upload_mb,
        }
