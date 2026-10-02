from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    document_ids: list[str] | None = Field(default=None, max_length=50)
    top_k: int | None = Field(default=None, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be blank")
        return v


class Source(BaseModel):
    index: int
    document_id: str
    filename: str
    file_type: str
    page: int | None = None
    row: int | None = None
    chunk_id: str
    location: str
    score: float
    text: str


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[Source]
    latency_ms: int
