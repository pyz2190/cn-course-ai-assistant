import json

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.models import ApiError


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "req-unknown")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error = ApiError(
        code=f"http_{exc.status_code}",
        message=str(exc.detail),
        request_id=_request_id(request),
        details=None,
    )
    return JSONResponse(status_code=exc.status_code, content=error.model_dump(mode="json"))


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    issues = exc.errors()
    for issue in issues:
        issue.pop("url", None)

    error = ApiError(
        code="validation_error",
        message="请求数据不符合接口契约。",
        request_id=_request_id(request),
        details={"errors": json.loads(json.dumps(issues, default=str))},
    )
    return JSONResponse(status_code=422, content=error.model_dump(mode="json"))
