from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Answer generation: "groq" (cloud) or "ollama" (local). Embeddings are always local.
    llm_provider: Literal["groq", "ollama"] = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_num_ctx: int = Field(8192, ge=2048)
    llm_timeout_seconds: int = Field(120, ge=5)

    embedding_model: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"

    chunk_size: int = Field(1000, ge=100, le=8000)
    chunk_overlap: int = Field(150, ge=0)
    top_k: int = Field(5, ge=1, le=20)
    relevance_threshold: float = Field(0.35, ge=0.0, le=1.0)

    max_upload_mb: int = Field(15, ge=1, le=200)
    max_chunks_per_document: int = Field(5000, ge=1)
    max_csv_rows: int = Field(20000, ge=1)
    embedding_batch_size: int = Field(32, ge=1, le=256)

    cors_origins: str = "http://localhost:5173"
    data_dir: Path = BACKEND_DIR / "data"
    collection_name: str = "documents"

    @model_validator(mode="after")
    def _check_overlap(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self

    @property
    def llm_model_name(self) -> str:
        return self.groq_model if self.llm_provider == "groq" else self.ollama_model

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def chroma_dir(self) -> Path:
        return Path(self.data_dir) / "chroma"

    @property
    def upload_tmp_dir(self) -> Path:
        return Path(self.data_dir) / "tmp"

    @property
    def db_path(self) -> Path:
        return Path(self.data_dir) / "app.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
