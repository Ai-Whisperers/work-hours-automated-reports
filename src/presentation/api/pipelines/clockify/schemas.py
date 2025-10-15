"""Clockify pipeline schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class TimeEntryQueryRequest(BaseModel):
    """Request model for querying time entries."""

    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    user_ids: Optional[List[str]] = Field(None, description="Filter by user IDs")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")


class TimeEntryResponse(BaseModel):
    """Response model for time entry."""

    id: str
    description: str
    start: str
    end: str
    duration_hours: float
    user_id: str
    user_name: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None


class TimeEntryBatchResponse(BaseModel):
    """Response model for batch time entry query."""

    time_entries: List[TimeEntryResponse]
    count: int
    total_hours: float


class ClockifyConnectionRequest(BaseModel):
    """Request model for testing Clockify connection."""

    api_key: str = Field(..., description="Clockify API key")
    workspace_id: str = Field(..., description="Workspace ID")


class ClockifyConnectionResponse(BaseModel):
    """Response model for Clockify connection test."""

    connected: bool
    workspace_id: str
    workspace_name: Optional[str] = None
    message: Optional[str] = None


class WorkspaceInfoResponse(BaseModel):
    """Response model for workspace information."""

    id: str
    name: str
    active_users: int = 0
