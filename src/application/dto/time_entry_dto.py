"""Time entry DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class TimeEntryDTO:
    """DTO for time entry data transfer."""

    id: str
    user_id: str
    user_name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    duration_hours: float
    billable: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    tags: List[str] = None
    work_item_ids: List[int] = None
    confidence_score: float = 0.0

    def __post_init__(self):
        """Initialize defaults."""
        if self.tags is None:
            self.tags = []
        if self.work_item_ids is None:
            self.work_item_ids = []


@dataclass
class TimeEntrySummaryDTO:
    """DTO for time entry summary data."""

    user_name: str
    total_hours: float
    entry_count: int
    billable_hours: float
    non_billable_hours: float
    matched_entries: int
    unmatched_entries: int
    projects: List[str]
    average_duration: float
