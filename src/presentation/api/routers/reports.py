"""Report generation endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ....infrastructure.config import get_settings
from ....infrastructure.api_clients import ClockifyClient, AzureDevOpsClient
from ....infrastructure.repositories import (
    ClockifyTimeEntryRepository,
    AzureDevOpsWorkItemRepository
)
from ....infrastructure.adapters import ExcelReportGenerator, HTMLReportGenerator
from ....domain.value_objects import DateRange
from ....domain.services import MatchingService
from ....application.use_cases import GenerateReportUseCase
from ....application.use_cases.generate_report_use_case import (
    GenerateReportRequest,
    ReportFormat
)
from ..middleware.websocket_manager import ws_manager


router = APIRouter()


# In-memory storage for report status (should use Redis in production)
report_status_store = {}


class ReportGenerationRequest(BaseModel):
    """Request model for report generation."""

    start_date: Optional[str] = Field(
        None,
        description="Start date in YYYY-MM-DD format. Default: 7 days ago"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in YYYY-MM-DD format. Default: today"
    )
    format: str = Field(
        "excel",
        description="Output format: excel, html, json"
    )
    user_ids: Optional[List[str]] = Field(
        None,
        description="Filter by user IDs"
    )
    project_ids: Optional[List[str]] = Field(
        None,
        description="Filter by project IDs"
    )
    include_unmatched: bool = Field(
        True,
        description="Include unmatched time entries"
    )


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


@router.post("/generate", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate a new report.

    Args:
        request: Report generation parameters
        background_tasks: FastAPI background tasks

    Returns:
        Report generation status
    """
    # Generate unique report ID
    report_id = str(uuid4())

    # Initialize status
    report_status_store[report_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "Report generation queued"
    }

    # Add background task
    background_tasks.add_task(
        generate_report_task,
        report_id,
        request
    )

    return ReportGenerationResponse(
        report_id=report_id,
        status="pending",
        message="Report generation started",
        websocket_url=f"/api/ws/report/{report_id}"
    )


@router.get("/status/{report_id}", response_model=ReportStatusResponse)
async def get_report_status(report_id: str):
    """Get report generation status.

    Args:
        report_id: Report ID

    Returns:
        Report status
    """
    if report_id not in report_status_store:
        raise HTTPException(status_code=404, detail="Report not found")

    status = report_status_store[report_id]

    response = ReportStatusResponse(
        report_id=report_id,
        status=status["status"],
        progress=status.get("progress"),
        message=status.get("message")
    )

    if status["status"] == "completed":
        response.download_url = f"/api/reports/download/{report_id}"

    if status["status"] == "failed":
        response.error = status.get("error")

    return response


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Download generated report.

    Args:
        report_id: Report ID

    Returns:
        Report file
    """
    if report_id not in report_status_store:
        raise HTTPException(status_code=404, detail="Report not found")

    status = report_status_store[report_id]

    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")

    file_path = status.get("file_path")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="application/octet-stream"
    )


async def generate_report_task(
    report_id: str,
    request: ReportGenerationRequest
):
    """Background task for report generation.

    Args:
        report_id: Report ID
        request: Report generation parameters
    """
    settings = get_settings()

    try:
        # Update status
        report_status_store[report_id]["status"] = "processing"
        report_status_store[report_id]["message"] = "Initializing..."
        report_status_store[report_id]["progress"] = 0.1

        # Broadcast via WebSocket
        await ws_manager.send_status_update(report_id, "processing", "Initializing...")
        await ws_manager.send_progress_update(report_id, 0.1, "Initializing...")

        # Parse dates
        if request.start_date:
            start = datetime.strptime(request.start_date, "%Y-%m-%d")
        else:
            start = datetime.now() - timedelta(days=7)

        if request.end_date:
            end = datetime.strptime(request.end_date, "%Y-%m-%d")
        else:
            end = datetime.now()

        date_range = DateRange(start, end)

        # Initialize clients
        report_status_store[report_id]["message"] = "Connecting to services..."
        report_status_store[report_id]["progress"] = 0.2

        await ws_manager.send_progress_update(report_id, 0.2, "Connecting to services...")

        clockify_client = ClockifyClient(settings)
        ado_client = AzureDevOpsClient(settings)

        # Create repositories
        time_entry_repo = ClockifyTimeEntryRepository(clockify_client)
        work_item_repo = AzureDevOpsWorkItemRepository(ado_client)

        # Create services
        matching_service = MatchingService()

        # Select report generator
        if request.format == "html":
            report_generator = HTMLReportGenerator()
        else:
            report_generator = ExcelReportGenerator()

        # Create cache service
        cache_service = None
        if settings.enable_caching:
            from ....infrastructure.adapters import LocalCacheService
            cache_service = LocalCacheService(settings.cache_directory)

        # Create use case
        use_case = GenerateReportUseCase(
            time_entry_repo=time_entry_repo,
            work_item_repo=work_item_repo,
            matching_service=matching_service,
            report_generator=report_generator,
            cache_service=cache_service
        )

        # Generate report
        report_status_store[report_id]["message"] = "Generating report..."
        report_status_store[report_id]["progress"] = 0.5

        await ws_manager.send_progress_update(report_id, 0.5, "Generating report...")

        output_path = Path(settings.report_output_directory) / f"report_{report_id}.{request.format}"

        use_case_request = GenerateReportRequest(
            date_range=date_range,
            format=ReportFormat(request.format),
            output_path=output_path,
            user_ids=request.user_ids,
            project_ids=request.project_ids,
            include_unmatched=request.include_unmatched,
            group_by=["user", "work_item"]
        )

        response = await use_case.execute(use_case_request)

        # Clean up
        await clockify_client.close()
        await ado_client.close()

        if response.success:
            report_status_store[report_id]["status"] = "completed"
            report_status_store[report_id]["message"] = "Report generated successfully"
            report_status_store[report_id]["progress"] = 1.0
            report_status_store[report_id]["file_path"] = str(response.report_path)

            # Broadcast completion via WebSocket
            await ws_manager.send_completion_update(
                report_id,
                f"/api/reports/download/{report_id}"
            )
        else:
            report_status_store[report_id]["status"] = "failed"
            report_status_store[report_id]["error"] = "; ".join(response.errors)

            # Broadcast failure via WebSocket
            await ws_manager.send_status_update(
                report_id,
                "failed",
                error="; ".join(response.errors)
            )

    except Exception as e:
        report_status_store[report_id]["status"] = "failed"
        report_status_store[report_id]["error"] = str(e)

        # Broadcast failure via WebSocket
        await ws_manager.send_status_update(report_id, "failed", error=str(e))
