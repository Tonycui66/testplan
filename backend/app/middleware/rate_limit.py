import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.redis_client import get_redis
from app.core.security import decode_access_token


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    def resolve_subject(self, request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            client = request.client.host if request.client else "unknown"
            return f"ip:{client}"
        subject = decode_access_token(authorization[7:].strip())
        return f"user:{subject}" if subject else f"ip:{request.client.host if request.client else 'unknown'}"

    async def count_request(self, subject: str) -> int:
        redis = get_redis()
        now = time.time()
        key = f"rate_limit:{subject}"
        window_start = now - 60
        member = str(uuid4())
        async with redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {member: now})
            pipe.zcard(key)
            pipe.expire(key, 60)
            results = await pipe.execute()
        return int(results[2] or 0)

    async def dispatch(self, request: Request, call_next) -> Response:
        subject = self.resolve_subject(request)
        try:
            count = await self.count_request(subject)
        except Exception:
            return await call_next(request)
        if count > self.requests_per_minute:
            return JSONResponse({"error": {"code": "RATE_LIMITED", "message": "Too many requests"}}, status_code=429)
        return await call_next(request)
