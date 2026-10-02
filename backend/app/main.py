import logging
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import Container, get_container
from app.routes import documents, query
from app.utils.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def _warm_up_embeddings() -> None:
    """Load the embedding model in the background so the first upload isn't slow."""
    try:
        warmup = getattr(get_container().embedder, "warmup", None)
        if warmup:
            warmup()
            log.info("Embedding model ready")
    except Exception as exc:  # noqa: BLE001
        log.warning("Embedding warm-up failed (will retry on first use): %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=_warm_up_embeddings, daemon=True).start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Intelligent Document Research Assistant", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError):
        if exc.status_code >= 500:
            log.error("%s: %s (cause: %r)", exc.code, exc.message, exc.__cause__)
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "message": e["msg"]}
            for e in exc.errors()
        ]
        return error_response(422, "validation_error", "The request is invalid.", details)

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        log.exception("Unhandled error: %s", exc)
        return error_response(500, "internal_error", AppError.default_message)

    @app.get("/api/health", tags=["health"])
    def health(c: Container = Depends(get_container)):
        settings = c.settings
        llm_ready = settings.llm_provider == "ollama" or bool(settings.groq_api_key)
        return {
            "status": "ok",
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model_name,
            "llm_configured": llm_ready,
            "embedding_model": settings.embedding_model,
        }

    app.include_router(documents.router)
    app.include_router(query.router)
    return app


app = create_app()
