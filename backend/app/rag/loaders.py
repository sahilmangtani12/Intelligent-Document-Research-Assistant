"""Turn an uploaded file into text segments that carry location metadata."""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.utils.errors import DocumentProcessingError, InvalidFileError


@dataclass
class Segment:
    """A logical unit of source text: one PDF page, one TXT file, or one CSV row."""

    text: str
    metadata: dict = field(default_factory=dict)


def load_pdf(path: Path) -> list[Segment]:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise DocumentProcessingError("This PDF is password-protected and can't be read.")
        segments = []
        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                segments.append(Segment(text, {"page": number}))
    except DocumentProcessingError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError, RecursionError) as exc:
        raise InvalidFileError("This PDF is corrupted or could not be parsed.") from exc
    if not segments:
        raise DocumentProcessingError(
            "No text could be extracted. Scanned or image-only PDFs aren't supported yet."
        )
    return segments


def load_txt(path: Path) -> list[Segment]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    text = text.strip()
    if not text:
        raise DocumentProcessingError("The text file contains no readable content.")
    return [Segment(text, {})]


def load_csv(path: Path, max_rows: int = 20000) -> list[Segment]:
    """One segment per data row, rendered as `column: value | column: value`.

    `row` is the spreadsheet row number (the header is row 1, first data row is row 2).
    """
    try:
        df = pd.read_csv(
            path, dtype=str, keep_default_na=False, encoding="utf-8-sig", sep=None, engine="python"
        )
    except pd.errors.EmptyDataError as exc:
        raise DocumentProcessingError("The CSV file contains no data.") from exc
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(
                path, dtype=str, keep_default_na=False, encoding="latin-1", sep=None, engine="python"
            )
        except Exception as exc:
            raise InvalidFileError("The CSV file could not be decoded.") from exc
    except (pd.errors.ParserError, pd.errors.DtypeWarning, ValueError) as exc:
        raise InvalidFileError("The CSV file is malformed and could not be parsed.") from exc

    if df.empty or len(df.columns) == 0:
        raise DocumentProcessingError("The CSV file has no data rows.")
    if len(df) > max_rows:
        raise DocumentProcessingError(f"The CSV has {len(df):,} rows; the limit is {max_rows:,}.")

    columns = [str(c).strip() for c in df.columns]
    segments = []
    for idx, values in enumerate(df.itertuples(index=False, name=None)):
        parts = [f"{c}: {str(v).strip()}" for c, v in zip(columns, values) if str(v).strip()]
        if parts:
            segments.append(Segment(" | ".join(parts), {"row": idx + 2}))
    if not segments:
        raise DocumentProcessingError("The CSV file has no non-empty rows.")
    return segments


def load_document(path: Path, file_type: str, *, max_csv_rows: int = 20000) -> list[Segment]:
    if file_type == "pdf":
        return load_pdf(path)
    if file_type == "txt":
        return load_txt(path)
    if file_type == "csv":
        return load_csv(path, max_rows=max_csv_rows)
    raise InvalidFileError(f"Unsupported file type: {file_type}")
