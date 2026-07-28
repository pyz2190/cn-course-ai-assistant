from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_resource_importer
from app.domain.models import ResourceImportRequest, ResourceImportResponse
from app.services.ports import ResourceImporter

router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("/import", response_model=ResourceImportResponse, status_code=status.HTTP_202_ACCEPTED)
def import_resource(
    request: ResourceImportRequest,
    importer: Annotated[ResourceImporter, Depends(get_resource_importer)],
) -> ResourceImportResponse:
    return importer.import_resource(request)
