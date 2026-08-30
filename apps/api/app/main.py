from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    events,
    exercises,
    feedback,
    health,
    knowledge_base,
    knowledge_points,
    qa,
    quality,
    resources,
    tasks,
)
from app.core.config import get_settings
from app.core.errors import http_exception_handler, validation_exception_handler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="计算机网络 AI 助教 API",
        version="0.1.0",
        description="完全独立于 Canvas 的离线优先项目骨架。",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req-{uuid4().hex}")
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(resources.router, prefix=prefix)
    app.include_router(qa.router, prefix=prefix)
    app.include_router(tasks.router, prefix=prefix)
    app.include_router(events.router, prefix=prefix)
    app.include_router(feedback.router, prefix=prefix)
    app.include_router(knowledge_base.router, prefix=prefix)
    app.include_router(knowledge_points.router, prefix=prefix)
    app.include_router(exercises.router, prefix=prefix)
    app.include_router(quality.router, prefix=prefix)
    return app


app = create_app()
