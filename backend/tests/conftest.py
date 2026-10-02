import hashlib
import math
import re

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import build_container, get_container
from app.main import create_app


class FakeEmbedder:
    """Deterministic bag-of-words embedder: texts sharing words have high cosine similarity."""

    DIM = 512

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.DIM
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.DIM] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class FakeLLM:
    def __init__(self):
        self.calls = []
        self.reply = None

    def generate_answer(self, question, chunks):
        self.calls.append((question, chunks))
        return self.reply or f"Answer based on the documents. [{1}]"


class FailingEmbedder(FakeEmbedder):
    def embed_documents(self, texts):
        from app.utils.errors import EmbeddingError

        raise EmbeddingError()


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        llm_provider="groq",
        groq_api_key="test",
        data_dir=tmp_path,
        relevance_threshold=0.3,
        max_upload_mb=1,
        chunk_size=300,
        chunk_overlap=50,
    )


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def container(settings, llm):
    return build_container(settings, embedder=FakeEmbedder(), llm=llm)


@pytest.fixture
def client(container):
    app = create_app()
    app.dependency_overrides[get_container] = lambda: container
    return TestClient(app)
