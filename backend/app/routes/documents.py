from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Response, UploadFile, status

from app.dependencies import Container, get_container
from app.schemas.documents import DocumentOut, DocumentSourcesOut, StatsOut
from app.utils.errors import InvalidFileError
from app.utils.validation import (
    get_file_type,
    sanitize_filename,
    save_upload_to_temp,
    validate_content,
)

router = APIRouter(prefix="/api", tags=["documents"])


@router.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    c: Container = Depends(get_container),
):
    """Validate, parse and chunk the file now; embed and index it in the background."""
    if not file.filename:
        raise InvalidFileError("The upload has no filename.")
    filename = sanitize_filename(file.filename)
    file_type = get_file_type(filename)
    path, size = save_upload_to_temp(
        file.file,
        max_bytes=c.settings.max_upload_bytes,
        tmp_dir=c.settings.upload_tmp_dir,
        suffix=f".{file_type}",
    )
    try:
        validate_content(path, file_type)
        record, chunks = c.documents.register(
            path=path, filename=filename, file_type=file_type, size_bytes=size
        )
    finally:
        path.unlink(missing_ok=True)  # raw uploads are never kept on disk
    background.add_task(c.documents.index, record, chunks)
    return record


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(c: Container = Depends(get_container)):
    return c.documents.list()


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, c: Container = Depends(get_container)):
    return c.documents.get(document_id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, c: Container = Depends(get_container)):
    c.documents.delete(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/documents/{document_id}/sources", response_model=DocumentSourcesOut)
def document_sources(
    document_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    c: Container = Depends(get_container),
):
    return c.documents.chunks(document_id, limit, offset)


@router.get("/stats", response_model=StatsOut)
def stats(c: Container = Depends(get_container)):
    return c.documents.stats()
