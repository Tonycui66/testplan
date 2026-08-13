from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging
from app.core.redis_client import get_redis
from app.dependencies import get_database_engine
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
    async def health(response: Response) -> dict:
        checks = {"database": "down", "redis": "down"}
        status_code = 200

        try:
            async with get_database_engine().connect() as connection:
                await connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            status_code = 503

        try:
            await get_redis().ping()
            checks["redis"] = "ok"
        except Exception:
            status_code = 503

        response.status_code = status_code
        return {
            "status": "ok" if status_code == 200 else "degraded",
            "version": settings.version,
            "checks": checks,
        }

    return app


app = create_app()
