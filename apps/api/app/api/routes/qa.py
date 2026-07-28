from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_qa_service
from app.domain.models import ApiError, AskRequest, AskResponse
from app.services.qa import QaService

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={422: {"model": ApiError, "description": "请求不符合接口契约"}},
)
def ask_question(
    request: AskRequest,
    service: Annotated[QaService, Depends(get_qa_service)],
) -> AskResponse:
    return service.ask(request)
