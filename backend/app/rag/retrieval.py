from dataclasses import dataclass

from app.services.embedding_service import Embedder
from app.services.vector_store import RetrievedChunk, VectorStore


@dataclass
class RetrievalResult:
    relevant: list[RetrievedChunk]  # passed the threshold, best first
    candidates: int  # how many chunks the vector search returned before filtering
    best_score: float


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore, top_k: int, threshold: float):
        self._embedder = embedder
        self._store = store
        self._top_k = top_k
        self._threshold = threshold

    def retrieve(
        self,
        question: str,
        *,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> RetrievalResult:
        vector = self._embedder.embed_query(question)
        found = self._store.query(vector, top_k or self._top_k, document_ids)
        found.sort(key=lambda c: c.score, reverse=True)
        relevant = [c for c in found if c.score >= self._threshold]
        return RetrievalResult(
            relevant=relevant,
            candidates=len(found),
            best_score=found[0].score if found else 0.0,
        )
