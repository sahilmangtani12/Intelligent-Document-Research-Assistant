from typing import Protocol

from app.config import Settings
from app.utils.errors import EmbeddingError


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class LocalEmbeddingService:
    """Embeddings computed on this machine with sentence-transformers (no API, no cost).

    The model is downloaded once from Hugging Face on first use, then cached on disk.
    Vectors are L2-normalised so cosine similarity in ChromaDB lies in [0, 1] for related text.
    """

    def __init__(self, settings: Settings, model=None):
        self._settings = settings
        self._model = model  # injectable for tests

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._settings.embedding_model)
            except Exception as exc:  # noqa: BLE001
                raise EmbeddingError(
                    "Could not load the local embedding model. On first run it must be downloaded "
                    "(about 90 MB), so check your internet connection and try again."
                ) from exc
        return self._model

    def warmup(self) -> None:
        self._get_model()

    def _encode(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        try:
            vectors = model.encode(
                texts,
                batch_size=self._settings.embedding_batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [list(map(float, v)) for v in vectors]
        except EmbeddingError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError("Embedding the text failed unexpectedly.") from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text])[0]
