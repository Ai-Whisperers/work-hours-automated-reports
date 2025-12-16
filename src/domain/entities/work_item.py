"""Work item entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..value_objects import WorkItemId


class WorkItemType(Enum):
    """Work item types from Azure DevOps."""

    EPIC = "Epic"
    FEATURE = "Feature"
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"
    ISSUE = "Issue"
    TEST_CASE = "Test Case"

    @classmethod
    def from_string(cls, value: str) -> Optional["WorkItemType"]:
        """Create WorkItemType from string, handling variations."""
        normalized = value.replace("-", " ").replace("_", " ").title()

        for item_type in cls:
            if item_type.value == normalized:
                return item_type

        # Try to match common variations
        if "story" in value.lower():
            return cls.USER_STORY
        if "bug" in value.lower():
            return cls.BUG
        if "task" in value.lower():
            return cls.TASK

        return None


class WorkItemState(Enum):
    """Work item states."""

    NEW = "New"
    ACTIVE = "Active"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REMOVED = "Removed"
    DONE = "Done"

    @property
    def is_active(self) -> bool:
        """Check if this is an active state."""
        return self in [self.NEW, self.ACTIVE, self.IN_PROGRESS]

    @property
    def is_completed(self) -> bool:
        """Check if this is a completed state."""
        return self in [self.RESOLVED, self.CLOSED, self.DONE]


@dataclass
class WorkItem:
    """Represents a work item from Azure DevOps.

    This is a domain entity that represents a unit of work
    that can be tracked and reported on.
    """

    id: WorkItemId
    title: str
    state: WorkItemState
    work_item_type: WorkItemType
    assigned_to: Optional[str] = None
    area_path: str = ""
    iteration_path: str = ""
    tags: List[str] = field(default_factory=list)
    parent_id: Optional[WorkItemId] = None

    # Effort/estimation fields
    story_points: Optional[float] = None
    effort: Optional[float] = None
    remaining_work: Optional[float] = None
    completed_work: Optional[float] = None

    # Metadata
    created_date: Optional[datetime] = None
    changed_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None

    # Additional fields from ADO
    _raw_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if work item is in an active state."""
        return self.state.is_active

    @property
    def is_completed(self) -> bool:
        """Check if work item is completed."""
        return self.state.is_completed

    @property
    def has_effort_estimate(self) -> bool:
        """Check if work item has any effort estimate."""
        return any(
            [
                self.story_points is not None,
                self.effort is not None,
                self.remaining_work is not None,
            ]
        )

    def get_effort_value(self) -> Optional[float]:
        """Get the most relevant effort value.

        Priority: story_points > effort > remaining_work
        """
        if self.story_points is not None:
            return self.story_points
        if self.effort is not None:
            return self.effort
        if self.remaining_work is not None:
            return self.remaining_work
        return None

    def get_iteration(self) -> str:
        """Extract iteration name from path."""
        if not self.iteration_path:
            return ""

        # Iteration path format: ProjectName\Iteration\Sprint 1
        parts = self.iteration_path.split("\\")
        return parts[-1] if parts else ""

    def get_area(self) -> str:
        """Extract area name from path."""
        if not self.area_path:
            return ""

        # Area path format: ProjectName\Area\SubArea
        parts = self.area_path.split("\\")
        return "\\".join(parts[1:]) if len(parts) > 1 else ""

    def has_tag(self, tag: str) -> bool:
        """Check if work item has a specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": int(self.id),
            "title": self.title,
            "state": self.state.value,
            "type": self.work_item_type.value,
            "assigned_to": self.assigned_to,
            "area_path": self.area_path,
            "iteration_path": self.iteration_path,
            "tags": self.tags,
            "parent_id": int(self.parent_id) if self.parent_id else None,
            "story_points": self.story_points,
            "effort": self.effort,
            "remaining_work": self.remaining_work,
            "completed_work": self.completed_work,
            "created_date": (
                self.created_date.isoformat() if self.created_date else None
            ),
            "changed_date": (
                self.changed_date.isoformat() if self.changed_date else None
            ),
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
        }

    @classmethod
    def from_ado_data(cls, data: dict) -> "WorkItem":
        """Create WorkItem from Azure DevOps API response.

        Args:
            data: Dictionary from Azure DevOps API

        Returns:
            WorkItem instance
        """
        fields = data.get("fields", {})

        # Parse work item ID
        work_item_id = WorkItemId(data["id"])

        # Parse work item type
        type_str = fields.get("System.WorkItemType", "Task")
        work_item_type = WorkItemType.from_string(type_str) or WorkItemType.TASK

        # Parse state
        state_str = fields.get("System.State", "New")
        state = WorkItemState.NEW
        for s in WorkItemState:
            if s.value.lower() == state_str.lower():
                state = s
                break

        # Parse assigned to
        assigned_to = None
        assignee = fields.get("System.AssignedTo")
        if assignee:
            if isinstance(assignee, dict):
                assigned_to = assignee.get("displayName") or assignee.get("uniqueName")
            else:
                assigned_to = str(assignee)

        # Parse tags
        tags = []
        tags_str = fields.get("System.Tags", "")
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(";") if tag.strip()]

        # Parse parent ID
        parent_id = None
        if "System.Parent" in fields:
            try:
                parent_id = WorkItemId(int(fields["System.Parent"]))
            except (ValueError, TypeError):
                pass

        # Parse dates
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return None

        created_date = parse_date(fields.get("System.CreatedDate"))
        changed_date = parse_date(fields.get("System.ChangedDate"))
        closed_date = parse_date(fields.get("Microsoft.VSTS.Common.ClosedDate"))

        return cls(
            id=work_item_id,
            title=fields.get("System.Title", ""),
            state=state,
            work_item_type=work_item_type,
            assigned_to=assigned_to,
            area_path=fields.get("System.AreaPath", ""),
            iteration_path=fields.get("System.IterationPath", ""),
            tags=tags,
            parent_id=parent_id,
            story_points=fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
            effort=fields.get("Microsoft.VSTS.Scheduling.Effort"),
            remaining_work=fields.get("Microsoft.VSTS.Scheduling.RemainingWork"),
            completed_work=fields.get("Microsoft.VSTS.Scheduling.CompletedWork"),
            created_date=created_date,
            changed_date=changed_date,
            closed_date=closed_date,
            _raw_fields=fields,
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"WorkItem(id={self.id}, type={self.work_item_type.value}, "
            f"state={self.state.value}, title={self.title[:30]}...)"
        )
