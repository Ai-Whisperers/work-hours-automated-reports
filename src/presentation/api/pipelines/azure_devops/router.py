"""Azure DevOps pipeline router."""

from fastapi import APIRouter, HTTPException, Depends

from .schemas import (
    WorkItemQueryRequest,
    WorkItemBatchResponse,
    ADOConnectionResponse
)
from .service import AzureDevOpsService


router = APIRouter()


def get_ado_service() -> AzureDevOpsService:
    """Dependency to get Azure DevOps service."""
    return AzureDevOpsService()


@router.get("/connection", response_model=ADOConnectionResponse)
async def check_connection(service: AzureDevOpsService = Depends(get_ado_service)):
    """Check Azure DevOps connection status.

    Returns:
        Connection status
    """
    try:
        connected = await service.test_connection()

        return ADOConnectionResponse(
            connected=connected,
            organization=service.settings.ado_organization,
            project=service.settings.ado_project,
            message="Connected successfully" if connected else "Connection failed"
        )
    finally:
        await service.close()


@router.post("/work-items", response_model=WorkItemBatchResponse)
async def get_work_items(
    request: WorkItemQueryRequest,
    service: AzureDevOpsService = Depends(get_ado_service)
):
    """Get work items by IDs.

    Args:
        request: Work item query request

    Returns:
        Work items data
    """
    try:
        result = await service.get_work_items(request.work_item_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
