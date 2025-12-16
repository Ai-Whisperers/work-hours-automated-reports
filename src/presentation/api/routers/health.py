"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from ....infrastructure.config import get_settings
from ....infrastructure.api_clients import ClockifyClient, AzureDevOpsClient


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str


class ServiceStatusResponse(BaseModel):
    """Service status response model."""

    clockify: bool
    azure_devops: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint.

    Returns:
        Health status
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment.value,
    )


@router.get("/health/services", response_model=ServiceStatusResponse)
async def check_services():
    """Check external service connections.

    Returns:
        Status of external services
    """
    settings = get_settings()

    clockify_client = ClockifyClient(settings)
    ado_client = AzureDevOpsClient(settings)

    try:
        clockify_status = await clockify_client.test_connection()
        ado_status = await ado_client.test_connection()

        return ServiceStatusResponse(clockify=clockify_status, azure_devops=ado_status)
    finally:
        await clockify_client.close()
        await ado_client.close()
