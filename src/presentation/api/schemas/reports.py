"""Report-related API schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ReportGenerationRequest(BaseModel):
    """Request model for report generation."""

    start_date: Optional[str] = Field(
        None, description="Start date in YYYY-MM-DD format. Default: 7 days ago"
    )
    end_date: Optional[str] = Field(
        None, description="End date in YYYY-MM-DD format. Default: today"
    )
    format: str = Field("excel", description="Output format: excel, html, json")
    user_ids: Optional[List[str]] = Field(None, description="Filter by user IDs")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
    include_unmatched: bool = Field(True, description="Include unmatched time entries")


class ReportGenerationResponse(BaseModel):
    """Response model for report generation."""

    report_id: str
    status: str
    message: str
    websocket_url: Optional[str] = None


class ReportStatusResponse(BaseModel):
    """Response model for report status."""

    report_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
