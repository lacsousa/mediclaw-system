from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class AppError(APIException):
    status_code = 400
    default_code = "APP_ERROR"

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.status_code = status_code
        self.default_code = code
        self.detail = {"code": code, "message": message, "details": details or {}}


class GuardrailBlockedError(AppError):
    def __init__(self, reason: str):
        super().__init__("GUARDRAIL_BLOCKED", reason, 200)


class LLMProviderError(AppError):
    def __init__(self, message: str):
        super().__init__("LLM_PROVIDER_ERROR", message, 502)


def envelope_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    payload = response.data
    if isinstance(payload, dict) and "code" in payload:
        response.data = {"data": None, "error": payload, "meta": {}}
    else:
        response.data = {
            "data": None,
            "error": {"code": "UNHANDLED", "message": str(payload)},
            "meta": {},
        }
    return response
