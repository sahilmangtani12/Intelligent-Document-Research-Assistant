"""SQLite registry for document records and query statistics (vectors live in ChromaDB)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_UPDATABLE = {"status", "error", "chunk_count", "unit_count"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    unit_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grounded INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_document(self, *, id: str, filename: str, file_type: str, size_bytes: int, unit_count: int) -> dict:
        with self._conn() as c:
            c.execute(
                "INSERT INTO documents (id, filename, file_type, size_bytes, status, unit_count, created_at) "
                "VALUES (?, ?, ?, ?, 'processing', ?, ?)",
                (id, filename, file_type, size_bytes, unit_count, _now()),
            )
        return self.get_document(id)

    def update_document(self, id: str, **fields) -> None:
        fields = {k: v for k, v in fields.items() if k in _UPDATABLE}
        if not fields:
            return
        sets = ", ".join(f"{k} = ?" for k in fields)
        with self._conn() as c:
            c.execute(f"UPDATE documents SET {sets} WHERE id = ?", (*fields.values(), id))

    def get_document(self, id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM documents WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def delete_document(self, id: str) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM documents WHERE id = ?", (id,)).rowcount > 0

    def record_query(self, grounded: bool, latency_ms: int) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO queries (grounded, latency_ms, created_at) VALUES (?, ?, ?)",
                (int(grounded), latency_ms, _now()),
            )

    def query_stats(self) -> dict:
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(grounded), 0) AS answered, "
                "COALESCE(AVG(latency_ms), 0) AS avg_latency FROM queries"
            ).fetchone()
        return {
            "total": row["total"],
            "answered": int(row["answered"]),
            "unanswered": row["total"] - int(row["answered"]),
            "avg_latency_ms": int(row["avg_latency"]),
        }
