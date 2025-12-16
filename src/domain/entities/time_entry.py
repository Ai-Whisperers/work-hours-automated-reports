"""Time entry entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from ..value_objects import Duration


@dataclass
class TimeEntry:
    """Represents a time tracking entry from Clockify.

    This is a domain entity with identity (id) that represents
    time spent by a user on a task.
    """

    id: str
    user_id: str
    user_name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    duration: Duration
    billable: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    workspace_id: Optional[str] = None

    # Domain-specific fields
    _extracted_work_item_ids: List[int] = field(default_factory=list)
    _confidence_score: float = 0.0

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if self.start_time >= self.end_time:
            raise ValueError(
                f"Start time {self.start_time} must be before end time {self.end_time}"
            )

        # Ensure duration matches the time range
        calculated_duration = Duration.from_seconds(
            (self.end_time - self.start_time).total_seconds()
        )

        # Allow small discrepancies due to rounding
        if abs(calculated_duration.seconds - self.duration.seconds) > 60:
            raise ValueError(
                f"Duration {self.duration} doesn't match time range "
                f"{self.start_time} to {self.end_time}"
            )

    @property
    def date(self) -> datetime:
        """Get the date of this entry (based on start time)."""
        return self.start_time.date()

    @property
    def has_description(self) -> bool:
        """Check if entry has a description."""
        return bool(self.description and self.description.strip())

    @property
    def extracted_work_item_ids(self) -> List[int]:
        """Get extracted work item IDs."""
        return self._extracted_work_item_ids.copy()

    def set_extracted_work_items(
        self, work_item_ids: List[int], confidence: float = 1.0
    ) -> None:
        """Set the extracted work item IDs with confidence score.

        Args:
            work_item_ids: List of extracted work item IDs
            confidence: Confidence score (0-1) for the extraction
        """
        self._extracted_work_item_ids = work_item_ids.copy()
        self._confidence_score = max(0.0, min(1.0, confidence))

    @property
    def confidence_score(self) -> float:
        """Get the confidence score for work item extraction."""
        return self._confidence_score

    @property
    def is_matched(self) -> bool:
        """Check if this entry has been matched to work items."""
        return len(self._extracted_work_item_ids) > 0

    def has_tag(self, tag: str) -> bool:
        """Check if entry has a specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_hours": self.duration.hours,
            "billable": self.billable,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "tags": self.tags,
            "workspace_id": self.workspace_id,
            "extracted_work_item_ids": self._extracted_work_item_ids,
            "confidence_score": self._confidence_score,
        }

    @classmethod
    def from_clockify_data(cls, data: dict) -> "TimeEntry":
        """Create TimeEntry from Clockify API response.

        Args:
            data: Dictionary from Clockify API

        Returns:
            TimeEntry instance
        """
        from datetime import datetime

        # Parse time interval
        time_interval = data.get("timeInterval", {})
        start = datetime.fromisoformat(time_interval["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(time_interval["end"].replace("Z", "+00:00"))

        # Parse duration
        duration_str = time_interval.get("duration", "PT0S")
        duration = Duration.from_iso8601(duration_str)

        # Extract user info
        user_name = data.get("userName", "Unknown")
        if not user_name and "user" in data:
            user_name = data["user"].get("name", "Unknown")

        # Extract project info
        project_id = data.get("projectId")
        project_name = None
        if "project" in data and data["project"]:
            project_name = data["project"].get("name")

        # Extract tags
        tags = []
        if "tags" in data and data["tags"]:
            tags = [
                tag.get("name", "") for tag in data["tags"] if isinstance(tag, dict)
            ]

        return cls(
            id=data["id"],
            user_id=data.get("userId", ""),
            user_name=user_name,
            description=data.get("description"),
            start_time=start,
            end_time=end,
            duration=duration,
            billable=data.get("billable", False),
            project_id=project_id,
            project_name=project_name,
            tags=tags,
            workspace_id=data.get("workspaceId"),
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"TimeEntry(id={self.id}, user={self.user_name}, "
            f"duration={self.duration}, description={self.description[:30] if self.description else 'None'}...)"
        )
