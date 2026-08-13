from collections import defaultdict
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._hits = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "unknown"
        now = monotonic()
        window = [hit for hit in self._hits[client] if now - hit < 60]
        self._hits[client] = window
        if len(window) >= self.requests_per_minute:
            return JSONResponse({"error": {"code": "rate_limited", "message": "Too many requests"}}, status_code=429)
        self._hits[client].append(now)
        return await call_next(request)
