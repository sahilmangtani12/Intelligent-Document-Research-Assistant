import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO

from app.utils.errors import (
    EmptyFileError,
    FileTooLargeError,
    InvalidFileError,
    UnsupportedFileTypeError,
)

ALLOWED_EXTENSIONS = {".pdf": "pdf", ".txt": "txt", ".csv": "csv"}
_CHUNK = 1024 * 1024
_SAFE_CHARS = re.compile(r"[^\w.\- ()]", re.UNICODE)


def sanitize_filename(name: str | None) -> str:
    """Strip any path components and unsafe characters from a client-supplied filename."""
    base = os.path.basename((name or "").replace("\\", "/"))
    base = _SAFE_CHARS.sub("_", base).strip(" .")
    return base[:120] or "upload"


def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError()
    return ALLOWED_EXTENSIONS[ext]


def save_upload_to_temp(
    stream: BinaryIO, *, max_bytes: int, tmp_dir: Path, suffix: str
) -> tuple[Path, int]:
    """Stream the upload to disk, enforcing the size limit without loading it into memory."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=tmp_dir, suffix=suffix)
    path, size = Path(name), 0
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := stream.read(_CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLargeError(
                        f"File is larger than the {max_bytes // (1024 * 1024)} MB limit."
                    )
                out.write(chunk)
        if size == 0:
            raise EmptyFileError()
        return path, size
    except Exception:
        path.unlink(missing_ok=True)
        raise


def validate_content(path: Path, file_type: str) -> None:
    """Cheap content sniffing so a renamed binary can't masquerade as an allowed type."""
    with open(path, "rb") as f:
        head = f.read(8192)
    if file_type == "pdf":
        if b"%PDF-" not in head[:1024]:
            raise InvalidFileError("This file is not a valid PDF.")
    elif b"\x00" in head:
        raise InvalidFileError(f"This file does not look like a valid {file_type.upper()} file.")
