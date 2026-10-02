"""Type-aware chunking: character windows for prose, one chunk per row for tables."""
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.loaders import Segment


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_prose(segments: list[Segment], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Split per segment so a chunk never crosses a page boundary (keeps page citations exact)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    for seg in segments:
        for piece in splitter.split_text(seg.text):
            if piece.strip():
                chunks.append(Chunk(piece.strip(), dict(seg.metadata)))
    return chunks


def chunk_rows(segments: list[Segment]) -> list[Chunk]:
    """CSV rows are already self-describing (`column: value`), so each row is one chunk."""
    return [Chunk(seg.text, dict(seg.metadata)) for seg in segments]


def chunk_segments(
    segments: list[Segment], file_type: str, *, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    if file_type == "csv":
        return chunk_rows(segments)
    return chunk_prose(segments, chunk_size, chunk_overlap)
