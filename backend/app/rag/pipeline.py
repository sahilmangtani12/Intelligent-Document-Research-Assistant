import re
import time

from app.rag.retrieval import Retriever
from app.schemas.query import QueryResponse, Source
from app.services.llm_service import LLM, NO_ANSWER, location_label
from app.services.vector_store import RetrievedChunk

FALLBACK_ANSWER = "I couldn't find relevant information in the uploaded documents."
_CITATION = re.compile(r"\[(\d+)\]")


def _to_source(index: int, chunk: RetrievedChunk) -> Source:
    m = chunk.metadata
    return Source(
        index=index,
        document_id=m.get("document_id", ""),
        filename=m.get("filename", "unknown"),
        file_type=m.get("file_type", ""),
        page=m.get("page"),
        row=m.get("row"),
        chunk_id=chunk.chunk_id,
        location=location_label(m),
        score=round(chunk.score, 4),
        text=chunk.text,
    )


class RAGPipeline:
    """question -> embed -> search -> threshold filter -> context -> LLM -> answer + sources."""

    def __init__(self, retriever: Retriever, llm: LLM):
        self._retriever = retriever
        self._llm = llm

    def answer(
        self, question: str, *, top_k: int | None = None, document_ids: list[str] | None = None
    ) -> QueryResponse:
        started = time.perf_counter()
        result = self._retriever.retrieve(question, top_k=top_k, document_ids=document_ids)

        def done(answer: str, grounded: bool, sources: list[Source]) -> QueryResponse:
            return QueryResponse(
                answer=answer,
                grounded=grounded,
                sources=sources,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        # Nothing cleared the threshold: never ask the LLM, so it can't invent an answer.
        if not result.relevant:
            return done(FALLBACK_ANSWER, False, [])

        text = self._llm.generate_answer(question, result.relevant)
        if text.strip().strip(".").upper() == NO_ANSWER:
            return done(FALLBACK_ANSWER, False, [])

        # Keep numbering stable (matches [n] in the answer) but show only the cited passages.
        cited = {int(n) for n in _CITATION.findall(text)}
        indexed = list(enumerate(result.relevant, start=1))
        shown = [(i, c) for i, c in indexed if i in cited] or indexed
        return done(text, True, [_to_source(i, c) for i, c in shown])
