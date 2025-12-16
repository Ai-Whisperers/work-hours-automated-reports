"""Report-related DTOs."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


@dataclass
class ReportRequest:
    """DTO for report generation requests."""

    start_date: datetime
    end_date: datetime
    output_format: str = "excel"
    output_path: Optional[Path] = None
    user_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None
    include_unmatched: bool = True
    group_by: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


@dataclass
class ReportStatistics:
    """DTO for report statistics."""

    total_entries: int
    matched_entries: int
    unmatched_entries: int
    match_rate: float
    total_hours: float
    unique_users: int
    unique_work_items: int
    average_confidence: float
    date_range: str
    generation_time: datetime


@dataclass
class ReportResponse:
    """DTO for report generation responses."""

    success: bool
    report_path: Optional[Path]
    statistics: Optional[ReportStatistics]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
