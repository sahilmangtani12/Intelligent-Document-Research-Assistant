# Intelligent Document Research Assistant

Upload PDF, TXT and CSV files, then ask questions in plain English. Answers are generated **only from your documents** and every answer cites the page, row or passage it came from.

It runs on **free** AI: embeddings are computed locally, and answers come from either **Groq** (free cloud API) or **Ollama** (fully local, no internet, no key).

## Screenshots
Add images to `docs/` and reference them here (dashboard, documents, research chat with sources).

## Problem statement
Finding one fact in long reports and spreadsheets is slow, and general chatbots confidently invent answers. This project retrieves the relevant passages from *your* files first, refuses to answer when nothing relevant exists, and shows its evidence.

## Features
- Drag-and-drop upload with progress; type, size, empty and corrupt-file validation
- PDF (page numbers), TXT, CSV (column names + spreadsheet row numbers)
- Type-aware chunking: configurable size/overlap for prose, one chunk per row for CSV
- Local sentence-transformers embeddings stored in ChromaDB with metadata
- Semantic search, configurable **relevance threshold**, safe **fallback** (the LLM is not called when nothing is relevant)
- Grounded answers with inline `[n]` citations; sources viewable in full
- Dashboard, document manager (preview passages, delete), chat with document-scope filter, dark mode

## Two ways to run the answer model
| | Embeddings | Answers | Internet | Cost |
|---|---|---|---|---|
| `LLM_PROVIDER=groq` | local | Groq cloud (Llama 3.3 70B) | needed for answers | free tier |
| `LLM_PROVIDER=ollama` | local | Ollama on your PC (Llama 3.1 8B) | not needed | free |

Switching between them needs **no re-upload**. Only changing `EMBEDDING_MODEL` does.

## Architecture
```
React (Vite, Tailwind) ──HTTP/JSON──▶ FastAPI
                                        ├─ routes/     HTTP only
                                        ├─ services/   document, embedding, vector_store, llm
                                        ├─ rag/        loaders → chunking → retrieval → pipeline
                                        ├─ models/     SQLite registry
                                        └─ ChromaDB  +  sentence-transformers (local)  +  Groq | Ollama
```

## RAG pipeline
```
Upload → validate → load (page/row metadata) → chunk → local embeddings → ChromaDB   (embedding runs in background)

Question → embed → ChromaDB top-K (cosine) → drop chunks below threshold
         → none left? → fallback message (no LLM call)
         → else       → numbered context → Groq/Ollama (context-only prompt) → answer + [n] citations → sources
```

## Tech stack
React 18, Vite, Tailwind CSS 4, React Router, Axios, Lucide · Python, FastAPI, Pydantic, Uvicorn · LangChain (text splitters, ChatGroq, ChatOllama), sentence-transformers, ChromaDB · pypdf, pandas · Docker, pytest

## Quick start (VS Code, Windows)
Requirements: Python 3.11 or 3.12, Node.js 20+, Git. For answers: a free Groq key **or** Ollama.

1. Open the project folder in VS Code (File → Open Folder → `doc-research-assistant`).
2. **Backend.** Open a terminal (Terminal → New Terminal):
   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   copy .env.example .env
   ```
   If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.
3. Edit `backend/.env` (see *Choosing the answer model* below).
4. `uvicorn app.main:app --reload --port 8000`. Leave it running. API docs: http://localhost:8000/docs
5. **Frontend.** Open a second terminal:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
6. Open http://localhost:5173.

macOS/Linux: use `python3 -m venv .venv`, `source .venv/bin/activate` and `cp .env.example .env`.

The first backend start downloads the embedding model (~90 MB) once.

## Choosing the answer model
**Groq (free cloud).** Create an account at https://console.groq.com, open *API Keys*, create a key, then in `backend/.env`:
```
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
```
Free-tier limits apply (per-minute and daily token caps; they change, see Groq's docs). If you hit them, set `GROQ_MODEL=llama-3.1-8b-instant`.

**Ollama (fully local).**
1. Install from https://ollama.com/download (Windows installer, macOS app, or Linux script).
2. In a terminal: `ollama pull llama3.1:8b` (about 5 GB, once).
3. Check `http://localhost:11434` shows "Ollama is running".
4. In `backend/.env`: `LLM_PROVIDER=ollama`, then restart the backend.

On a CPU-only laptop, if answers are slow use `OLLAMA_MODEL=llama3.2:3b` (`ollama pull llama3.2:3b`).

## Environment variables (backend/.env)
| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` or `ollama` |
| `GROQ_API_KEY` / `GROQ_MODEL` | – / `llama-3.3-70b-versatile` | Groq settings (server-side only) |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `llama3.1:8b` | Ollama settings |
| `OLLAMA_NUM_CTX` | 8192 | Context window; must fit your retrieved passages |
| `EMBEDDING_MODEL` | `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` | Local embedding model |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 150 | Prose chunking (characters) |
| `TOP_K` | 5 | Chunks retrieved per question |
| `RELEVANCE_THRESHOLD` | 0.35 | Minimum cosine similarity. **Tune this** |
| `MAX_UPLOAD_MB`, `MAX_CHUNKS_PER_DOCUMENT`, `MAX_CSV_ROWS` | 15, 5000, 20000 | Limits |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed browser origins |
| `DATA_DIR` | `./data` | SQLite + Chroma storage |

Frontend: `VITE_API_URL` (empty in development, public backend URL in production).

## Docker
```bash
cp backend/.env.example backend/.env     # set LLM_PROVIDER and key
docker compose up --build
```
UI: http://localhost:3000 · API: http://localhost:8000. The embedding model is baked into the image. For `LLM_PROVIDER=ollama` the container reaches Ollama on your host via `host.docker.internal`; on Linux you may need Ollama to listen on all interfaces (`OLLAMA_HOST=0.0.0.0`). Running the backend directly (Quick start) is simpler for Ollama.

## Deployment
- **Backend → Render** (`render.yaml`): use Groq (Ollama needs your own hardware). The embedding model needs roughly 1–2 GB RAM, so choose a 2 GB+ instance, and keep the persistent disk or the index is lost on redeploy.
- **Frontend → Vercel:** import `frontend/`, set `VITE_API_URL` to the Render URL; set `CORS_ORIGINS` on the backend to the Vercel URL.
- Run a single backend instance (embedded Chroma is not multi-writer).

## API
Errors always look like `{"error": {"code": "...", "message": "..."}}`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/documents/upload` | Multipart `file`. `202`, status `processing` |
| GET | `/api/documents` | List documents |
| GET | `/api/documents/{id}` | One document (poll `status`) |
| DELETE | `/api/documents/{id}` | `204`; removes record and vectors |
| GET | `/api/documents/{id}/sources` | Indexed passages with page/row |
| POST | `/api/query` | `{question, document_ids?, top_k?}` → answer + sources |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/health` | Provider and model info |

Codes: `400` invalid/empty file · `413` too large · `415` unsupported type · `422` unreadable content or bad request · `404` not found · `502` LLM/embedding failure · `503` vector store or config problem.

```bash
curl -F "file=@annual_report.pdf" http://localhost:8000/api/documents/upload
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" \
  -d '{"question": "What was the revenue in 2025?"}'
```
```json
{"answer": "Revenue increased to $15 million in 2025. [1]", "grounded": true,
 "sources": [{"index": 1, "filename": "annual_report.pdf", "page": 12, "location": "Page 12", "score": 0.71, "text": "…"}],
 "latency_ms": 1432}
```
CSV sources report the spreadsheet row (header = row 1, first data row = row 2).

## Testing
```bash
cd backend && pytest
```
61 tests cover parsing, chunking, vector search, the threshold and fallback, citations, provider error handling, and API/error paths. They use fakes, so no API key, model download or network is needed.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Groq rejected the API key" | Check `GROQ_API_KEY` in `backend/.env`; restart the backend |
| "Couldn't reach Ollama" | Open the Ollama app / run `ollama serve`; check `OLLAMA_BASE_URL` |
| "Ollama doesn't have the model" | `ollama pull llama3.1:8b` |
| First upload is slow | The embedding model is downloading once |
| Always "couldn't find relevant information" | Lower `RELEVANCE_THRESHOLD` (e.g. 0.25) |
| Irrelevant answers | Raise `RELEVANCE_THRESHOLD` (e.g. 0.45) |
| Frontend can't reach backend | Backend must run on port 8000; check CORS_ORIGINS |

## Known limitations
No OCR for scanned PDFs; no authentication or per-user isolation; single backend instance; answer quality with small local models is lower than large cloud models.

## Future improvements
OCR · user accounts · streaming answers · hybrid (BM25 + vector) search and reranking · conversation memory · DOCX/Markdown · hosted vector DB for scale · retrieval evaluation set.
