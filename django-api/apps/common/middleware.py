import time
import uuid

import structlog

from apps.common.logging_config import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        structlog.contextvars.clear_contextvars()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = rid
        structlog.contextvars.bind_contextvars(request_id=rid)

        start = time.perf_counter()
        try:
            response = self.get_response(request)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request_completed",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
            response["X-Request-ID"] = rid
            return response
        except Exception:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.path,
                latency_ms=latency_ms,
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()


class UserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            structlog.contextvars.bind_contextvars(user_id=request.user.id)
        return self.get_response(request)
