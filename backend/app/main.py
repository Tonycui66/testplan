from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    setup_cors(app)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": type(exc).__name__, "message": exc.message}},
        )

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict:
        return {
            "status": "ok",
            "version": settings.version,
            "database": "configured",
            "redis": "configured",
        }

    return app


app = create_app()
