"""Clockify pipeline router."""

from fastapi import APIRouter, HTTPException, Depends

from .schemas import (
    TimeEntryQueryRequest,
    TimeEntryBatchResponse,
    ClockifyConnectionRequest,
    ClockifyConnectionResponse
)
from .service import ClockifyService


router = APIRouter()


def get_clockify_service() -> ClockifyService:
    """Dependency to get Clockify service."""
    return ClockifyService()


@router.post("/connection", response_model=ClockifyConnectionResponse)
async def check_connection(
    request: ClockifyConnectionRequest,
    service: ClockifyService = Depends(get_clockify_service)
):
    """Check Clockify connection status.

    Args:
        request: Connection request with credentials

    Returns:
        Connection status
    """
    try:
        connected = await service.test_connection()

        return ClockifyConnectionResponse(
            connected=connected,
            workspace_id=service.settings.clockify_workspace_id,
            message="Connected successfully" if connected else "Connection failed"
        )
    finally:
        await service.close()


@router.post("/time-entries", response_model=TimeEntryBatchResponse)
async def get_time_entries(
    request: TimeEntryQueryRequest,
    service: ClockifyService = Depends(get_clockify_service)
):
    """Get time entries for a date range.

    Args:
        request: Time entry query request

    Returns:
        Time entries data
    """
    try:
        result = await service.get_time_entries(
            start_date=request.start_date,
            end_date=request.end_date,
            user_ids=request.user_ids,
            project_ids=request.project_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
