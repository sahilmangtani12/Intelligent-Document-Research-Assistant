"""Composition root: builds the object graph once. Tests override `get_container`."""
from dataclasses import dataclass
from functools import lru_cache

from app.config import Settings, get_settings
from app.models.database import Database
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval import Retriever
from app.services.document_service import DocumentService
from app.services.embedding_service import Embedder, LocalEmbeddingService
from app.services.llm_service import LLM, ChatLLMService
from app.services.vector_store import VectorStore


@dataclass
class Container:
    settings: Settings
    db: Database
    store: VectorStore
    documents: DocumentService
    pipeline: RAGPipeline
    embedder: Embedder


def build_container(settings: Settings, embedder: Embedder | None = None, llm: LLM | None = None) -> Container:
    embedder = embedder or LocalEmbeddingService(settings)
    llm = llm or ChatLLMService(settings)
    db = Database(settings.db_path)
    store = VectorStore(settings.chroma_dir, settings.collection_name)
    retriever = Retriever(embedder, store, settings.top_k, settings.relevance_threshold)
    return Container(
        settings=settings,
        db=db,
        store=store,
        documents=DocumentService(db, store, embedder, settings),
        pipeline=RAGPipeline(retriever, llm),
        embedder=embedder,
    )


@lru_cache
def get_container() -> Container:
    return build_container(get_settings())
