import pytest

from tests.test_loaders import make_pdf


def upload(client, name, data, ctype="application/octet-stream"):
    return client.post("/api/documents/upload", files={"file": (name, data, ctype)})


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_upload_txt_becomes_ready_and_is_listed(client):
    r = upload(client, "notes.txt", b"The launch date is March 3rd. Budget is 40k.")
    assert r.status_code == 202
    doc = client.get(f"/api/documents/{r.json()['id']}").json()
    assert doc["status"] == "ready" and doc["chunk_count"] >= 1
    assert len(client.get("/api/documents").json()) == 1


def test_upload_pdf_and_query_with_page_citation(client, tmp_path):
    p = tmp_path / "annual_report.pdf"
    make_pdf(p, ["Intro page", "Revenue increased to 15 million in 2025"])
    assert upload(client, "annual_report.pdf", p.read_bytes()).status_code == 202
    body = client.post("/api/query", json={"question": "what was revenue in 2025"}).json()
    assert body["grounded"] is True
    assert body["sources"][0]["filename"] == "annual_report.pdf"
    assert body["sources"][0]["page"] == 2


def test_query_fallback_for_unrelated_question(client):
    upload(client, "n.txt", b"The launch date is March 3rd.")
    body = client.post("/api/query", json={"question": "zebra giraffe savannah migration"}).json()
    assert body["grounded"] is False and body["sources"] == []


def test_delete_removes_document_and_vectors(client, container):
    doc_id = upload(client, "n.txt", b"temporary content here").json()["id"]
    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
    assert container.store.count() == 0


def test_delete_unknown_document_is_404(client):
    r = client.delete("/api/documents/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_document_sources_endpoint(client):
    doc_id = upload(client, "s.csv", b"region,revenue\nEMEA,100\nAPAC,250\n").json()["id"]
    body = client.get(f"/api/documents/{doc_id}/sources").json()
    assert body["total_chunks"] == 2
    assert body["chunks"][0]["row"] == 2 and "region: EMEA" in body["chunks"][0]["text"]


def test_stats_counts_documents_and_queries(client):
    upload(client, "n.txt", b"hello world document")
    client.post("/api/query", json={"question": "hello world"})
    s = client.get("/api/stats").json()
    assert s["documents_ready"] == 1 and s["queries_total"] == 1 and s["by_type"] == {"txt": 1}


@pytest.mark.parametrize(
    "name,data,status,code",
    [
        ("malware.exe", b"MZ....", 415, "unsupported_file_type"),
        ("noext", b"hello", 415, "unsupported_file_type"),
        ("empty.txt", b"", 400, "empty_file"),
        ("fake.pdf", b"just text pretending", 400, "invalid_file"),
        ("corrupt.pdf", b"%PDF-1.4 garbage", 400, "invalid_file"),
        ("bin.txt", b"abc\x00\x01\x02", 400, "invalid_file"),
        ("blank.txt", b"   \n  ", 422, "processing_failed"),
        ("header_only.csv", b"a,b\n", 422, "processing_failed"),
    ],
)
def test_invalid_uploads(client, name, data, status, code):
    r = upload(client, name, data)
    assert r.status_code == status
    assert r.json()["error"]["code"] == code


def test_oversized_upload_rejected(client):
    r = upload(client, "big.txt", b"a" * (1024 * 1024 + 1))
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"


def test_filename_path_traversal_is_sanitised(client):
    r = upload(client, "../../etc/passwd.txt", b"some harmless text")
    assert r.status_code == 202 and r.json()["filename"] == "passwd.txt"


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 2001}, {"question": "ok", "top_k": 0}])
def test_invalid_query_payloads(client, payload):
    r = client.post("/api/query", json=payload)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_embedding_failure_marks_document_failed(settings, llm):
    from fastapi.testclient import TestClient

    from app.dependencies import build_container, get_container
    from app.main import create_app
    from tests.conftest import FailingEmbedder

    container = build_container(settings, embedder=FailingEmbedder(), llm=llm)
    app = create_app()
    app.dependency_overrides[get_container] = lambda: container
    c = TestClient(app)
    doc_id = upload(c, "n.txt", b"some text to embed").json()["id"]
    doc = c.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "failed" and "embedding" in doc["error"].lower()
    assert container.store.count() == 0


def test_llm_failure_returns_502(client, llm):
    from app.utils.errors import LLMError

    upload(client, "n.txt", b"revenue grew fifteen million")

    def boom(*a, **k):
        raise LLMError()

    llm.generate_answer = boom
    r = client.post("/api/query", json={"question": "revenue grew"})
    assert r.status_code == 502 and r.json()["error"]["code"] == "llm_failed"


def test_cors_allows_configured_origin(client):
    r = client.options(
        "/api/documents",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
