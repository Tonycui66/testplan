import json
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
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
from app.modules.pipeline.router import router as pipeline_router, ws_router as pipeline_ws_router
from app.modules.artifact.router import router as artifact_router
from app.modules.deploy.router import router as deploy_router
from app.modules.project.router import router as project_router
from app.modules.test.router import router as test_router
from app.modules.repo.router import router as repo_router, webhook_router as repo_webhook_router
from app.modules.user.router import router as user_router


ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def app_error_code(exc: AppError) -> str:
    return ERROR_CODES.get(exc.status_code, "APPLICATION_ERROR")


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

    app.include_router(user_router)
    app.include_router(project_router)
    app.include_router(repo_router)
    app.include_router(artifact_router)
    app.include_router(deploy_router)
    app.include_router(test_router)
    app.include_router(repo_webhook_router)
    app.include_router(pipeline_router)
    app.include_router(pipeline_ws_router)

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError):
        return error_response(exc.status_code, app_error_code(exc), exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        code = ERROR_CODES.get(exc.status_code, "APPLICATION_ERROR")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        return error_response(422, "VALIDATION_ERROR", "Request validation failed")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        return error_response(500, "INTERNAL_ERROR", "Unexpected server error")

    @app.middleware("http")
    async def response_envelope(request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/api/v1") or response.status_code >= 400:
            return response
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        if not body:
            return response
        try:
            payload: Any = json.loads(body)
        except Exception:
            return response
        if isinstance(payload, dict) and set(payload.keys()) == {"items", "meta"}:
            wrapped: Dict[str, Any] = {"data": payload["items"], "meta": payload["meta"]}
        else:
            wrapped = {"data": payload}
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return JSONResponse(content=wrapped, status_code=response.status_code, headers=headers)

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
