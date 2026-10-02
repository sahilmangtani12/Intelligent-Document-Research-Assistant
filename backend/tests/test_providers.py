import pytest

from app.config import Settings
from app.services.embedding_service import LocalEmbeddingService
from app.services.llm_service import (
    SYSTEM_PROMPT,
    ChatLLMService,
    build_user_prompt,
    describe_llm_error,
)
from app.services.vector_store import RetrievedChunk
from app.utils.errors import ConfigurationError, EmbeddingError, LLMError

CHUNKS = [RetrievedChunk("d:0", "Revenue was 15 million.", {"filename": "r.pdf", "page": 12}, 0.8)]


def make_settings(**kw):
    return Settings(_env_file=None, **kw)


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeChat:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.messages = reply, error, None

    def invoke(self, messages):
        self.messages = messages
        if self.error:
            raise self.error
        return FakeResponse(self.reply)


class StatusError(Exception):
    def __init__(self, status_code, msg="boom"):
        super().__init__(msg)
        self.status_code = status_code


def test_prompt_contains_numbered_context_with_source_and_question():
    prompt = build_user_prompt("What was revenue?", CHUNKS)
    assert "[1] (source: r.pdf, Page 12)" in prompt and "Revenue was 15 million." in prompt
    assert prompt.endswith("Question: What was revenue?")
    assert "ONLY" in SYSTEM_PROMPT and "NO_ANSWER" in SYSTEM_PROMPT


def test_llm_returns_text_and_sends_system_and_user_messages():
    chat = FakeChat("Revenue was 15 million. [1]")
    out = ChatLLMService(make_settings(), client=chat).generate_answer("q", CHUNKS)
    assert out == "Revenue was 15 million. [1]"
    assert [type(m).__name__ for m in chat.messages] == ["SystemMessage", "HumanMessage"]


def test_llm_handles_list_content_and_rejects_empty():
    assert ChatLLMService(make_settings(), client=FakeChat([{"text": "a"}, "b"])).generate_answer("q", CHUNKS) == "ab"
    with pytest.raises(LLMError):
        ChatLLMService(make_settings(), client=FakeChat("  ")).generate_answer("q", CHUNKS)


def test_groq_without_key_is_a_configuration_error():
    with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
        ChatLLMService(make_settings(llm_provider="groq", groq_api_key="")).generate_answer("q", CHUNKS)


@pytest.mark.parametrize(
    "provider,status,expected",
    [
        ("groq", 401, "rejected the API key"),
        ("groq", 429, "rate limit"),
        ("groq", 404, "doesn't recognise the model"),
        ("ollama", 404, "ollama pull"),
        ("ollama", None, "Make sure Ollama is running"),
    ],
)
def test_llm_errors_are_translated_to_actionable_messages(provider, status, expected):
    exc = StatusError(status) if status else ConnectionError("refused")
    assert expected in describe_llm_error(provider, "m", "http://localhost:11434", exc)


def test_auth_errors_are_not_retried_but_rate_limits_are(monkeypatch):
    monkeypatch.setattr("app.utils.retry.time.sleep", lambda s: None)
    calls = {"n": 0}

    class Counting(FakeChat):
        def invoke(self, messages):
            calls["n"] += 1
            raise StatusError(401)

    with pytest.raises(LLMError):
        ChatLLMService(make_settings(), client=Counting()).generate_answer("q", CHUNKS)
    assert calls["n"] == 1

    calls["n"] = 0

    class RateLimited(FakeChat):
        def invoke(self, messages):
            calls["n"] += 1
            raise StatusError(429)

    with pytest.raises(LLMError):
        ChatLLMService(make_settings(), client=RateLimited()).generate_answer("q", CHUNKS)
    assert calls["n"] == 2


def test_real_langchain_clients_can_be_constructed():
    """Catches wrong constructor arguments without making any network call."""
    g = ChatLLMService(make_settings(llm_provider="groq", groq_api_key="x"))._get_client()
    assert type(g).__name__ == "ChatGroq"
    o = ChatLLMService(make_settings(llm_provider="ollama"))._get_client()
    assert type(o).__name__ == "ChatOllama" and o.num_ctx == 8192


class FakeModel:
    def encode(self, texts, **kw):
        assert kw["normalize_embeddings"] is True
        return [[1.0, 0.0] for _ in texts]


def test_local_embedder_returns_float_lists():
    e = LocalEmbeddingService(make_settings(), model=FakeModel())
    assert e.embed_documents(["a", "b"]) == [[1.0, 0.0], [1.0, 0.0]]
    assert e.embed_query("a") == [1.0, 0.0]


def test_local_embedder_wraps_failures():
    class Broken:
        def encode(self, *a, **k):
            raise RuntimeError("oom")

    with pytest.raises(EmbeddingError):
        LocalEmbeddingService(make_settings(), model=Broken()).embed_query("x")


def test_config_rejects_overlap_larger_than_chunk_and_bad_provider():
    with pytest.raises(ValueError):
        make_settings(chunk_size=200, chunk_overlap=200)
    with pytest.raises(ValueError):
        make_settings(llm_provider="gemini")


def test_health_reports_provider(client):
    body = client.get("/api/health").json()
    assert body["llm_provider"] == "groq" and body["llm_configured"] is True
