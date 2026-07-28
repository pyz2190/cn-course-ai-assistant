from fastapi import APIRouter

from app.domain.models import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cn-course-ai-assistant-api", mode="mock")
