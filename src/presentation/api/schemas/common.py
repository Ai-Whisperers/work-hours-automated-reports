"""Common API schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str


class ServiceStatusResponse(BaseModel):
    """Service status response model."""

    clockify: bool
    azure_devops: bool


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: Optional[dict] = None


class ProgressUpdate(BaseModel):
    """Progress update model for WebSocket."""

    type: str = "progress"
    report_id: str
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    message: str


class StatusUpdate(BaseModel):
    """Status update model for WebSocket."""

    type: str = "status"
    report_id: str
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    message: Optional[str] = None
    error: Optional[str] = None
