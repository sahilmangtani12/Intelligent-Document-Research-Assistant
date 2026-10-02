"""All ChromaDB access lives here. Routes and the pipeline never touch Chroma directly."""
from dataclasses import dataclass
from pathlib import Path

import chromadb

from app.utils.errors import VectorStoreError


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    score: float  # cosine similarity in [0, 1]; higher is more similar


class VectorStore:
    def __init__(self, persist_dir: Path, collection_name: str = "documents"):
        try:
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_dir))
            self._collection = self._client.get_or_create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc

    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict],
        batch_size: int = 500,
    ) -> None:
        try:
            for i in range(0, len(ids), batch_size):
                s = slice(i, i + batch_size)
                self._collection.add(
                    ids=ids[s], embeddings=embeddings[s], documents=texts[s], metadatas=metadatas[s]
                )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc

    def query(
        self, embedding: list[float], top_k: int, document_ids: list[str] | None = None
    ) -> list[RetrievedChunk]:
        where = None
        if document_ids:
            where = (
                {"document_id": document_ids[0]}
                if len(document_ids) == 1
                else {"document_id": {"$in": document_ids}}
            )
        try:
            total = self._collection.count()
            if total == 0:
                return []
            res = self._collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, total),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc
        results = []
        for cid, doc, meta, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            score = max(0.0, min(1.0, 1.0 - float(dist)))
            results.append(RetrievedChunk(cid, doc, meta or {}, score))
        return results

    def delete_document(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc

    def get_document_chunks(self, document_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        try:
            res = self._collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"],
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc
        items = [
            {"chunk_id": i, "text": d, "metadata": m or {}}
            for i, d, m in zip(res["ids"], res["documents"], res["metadatas"])
        ]
        items.sort(key=lambda x: x["metadata"].get("chunk_index", 0))
        return items[offset : offset + limit]

    def count(self) -> int:
        try:
            return self._collection.count()
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError() from exc
