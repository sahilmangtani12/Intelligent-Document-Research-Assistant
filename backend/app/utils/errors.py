"""Application errors. Each maps to an HTTP status and a stable machine-readable code."""


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    default_message = "Something went wrong on our side. Please try again."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidFileError(AppError):
    status_code, code = 400, "invalid_file"
    default_message = "The uploaded file is not valid."


class EmptyFileError(AppError):
    status_code, code = 400, "empty_file"
    default_message = "The uploaded file is empty."


class FileTooLargeError(AppError):
    status_code, code = 413, "file_too_large"
    default_message = "The uploaded file exceeds the size limit."


class UnsupportedFileTypeError(AppError):
    status_code, code = 415, "unsupported_file_type"
    default_message = "Unsupported file type. Upload a PDF, TXT or CSV file."


class DocumentProcessingError(AppError):
    status_code, code = 422, "processing_failed"
    default_message = "We couldn't read any content from this document."


class NotFoundError(AppError):
    status_code, code = 404, "not_found"
    default_message = "Resource not found."


class EmbeddingError(AppError):
    status_code, code = 502, "embedding_failed"
    default_message = "The embedding service is unavailable. Please try again shortly."


class LLMError(AppError):
    status_code, code = 502, "llm_failed"
    default_message = "The language model is unavailable. Please try again shortly."


class VectorStoreError(AppError):
    status_code, code = 503, "vector_store_failed"
    default_message = "The document index is unavailable. Please try again shortly."


class ConfigurationError(AppError):
    status_code, code = 503, "not_configured"
    default_message = "The server is not configured correctly."
