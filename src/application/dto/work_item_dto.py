"""Work item DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class WorkItemDTO:
    """DTO for work item data transfer."""

    id: int
    title: str
    state: str
    work_item_type: str
    assigned_to: Optional[str]
    area_path: str
    iteration_path: str
    tags: List[str]
    parent_id: Optional[int] = None
    story_points: Optional[float] = None
    effort: Optional[float] = None
    created_date: Optional[datetime] = None
    changed_date: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.tags is None:
            self.tags = []


@dataclass
class WorkItemSummaryDTO:
    """DTO for work item summary data."""

    work_item_id: int
    title: str
    work_item_type: str
    state: str
    total_hours: float
    unique_contributors: int
    entry_count: int
    first_entry_date: datetime
    last_entry_date: datetime
    completion_percentage: float = 0.0
