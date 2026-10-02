from app.rag.pipeline import FALLBACK_ANSWER
from tests.conftest import FakeEmbedder


def index(container, filename, file_type, texts, metas):
    from app.rag.chunking import Chunk

    doc = container.db.create_document(
        id=filename, filename=filename, file_type=file_type, size_bytes=1, unit_count=1
    )
    container.documents.index(doc, [Chunk(t, m) for t, m in zip(texts, metas)])


def test_vector_store_scores_similar_text_higher(container):
    index(container, "n.txt", "txt", ["revenue grew to fifteen million", "the cat sat on the mat"], [{}, {}])
    emb = FakeEmbedder()
    res = container.store.query(emb.embed_query("revenue million"), top_k=2)
    assert res[0].text.startswith("revenue")
    assert res[0].score > res[1].score
    assert res[0].metadata["filename"] == "n.txt"


def test_relevant_question_calls_llm_and_returns_sources(container, llm):
    index(container, "r.pdf", "pdf", ["revenue grew to fifteen million in 2025"], [{"page": 12}])
    out = container.pipeline.answer("what was the revenue in 2025")
    assert out.grounded and len(llm.calls) == 1
    assert out.sources[0].page == 12 and out.sources[0].location == "Page 12"


def test_below_threshold_returns_fallback_without_calling_llm(container, llm):
    index(container, "r.pdf", "pdf", ["revenue grew to fifteen million"], [{"page": 1}])
    out = container.pipeline.answer("quantum chromodynamics lattice gauge")
    assert out.answer == FALLBACK_ANSWER
    assert not out.grounded and out.sources == []
    assert llm.calls == []


def test_empty_index_returns_fallback(container, llm):
    out = container.pipeline.answer("anything at all")
    assert out.answer == FALLBACK_ANSWER and llm.calls == []


def test_model_no_answer_sentinel_becomes_fallback(container, llm):
    index(container, "r.txt", "txt", ["revenue grew fifteen million"], [{}])
    llm.reply = "NO_ANSWER"
    out = container.pipeline.answer("what was the revenue")
    assert out.answer == FALLBACK_ANSWER and not out.grounded


def test_only_cited_sources_are_returned(container, llm):
    index(container, "a.txt", "txt", ["revenue grew fifteen million", "revenue costs and profit table"], [{}, {}])
    llm.reply = "Revenue grew [2]."
    out = container.pipeline.answer("revenue", top_k=2)
    assert [s.index for s in out.sources] == [2]


def test_document_filter_limits_search(container):
    index(container, "a.txt", "txt", ["revenue grew fifteen million"], [{}])
    index(container, "b.txt", "txt", ["revenue fell to two million"], [{}])
    out = container.pipeline.answer("revenue", document_ids=["b.txt"])
    assert {s.filename for s in out.sources} == {"b.txt"}


def test_csv_citation_reports_row(container):
    index(container, "s.csv", "csv", ["region: EMEA | revenue: 100"], [{"row": 24}])
    out = container.pipeline.answer("EMEA revenue")
    assert out.sources[0].location == "Row 24"
