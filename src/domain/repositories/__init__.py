"""Domain repository interfaces (ports).

These are abstractions that define how the domain interacts with
external data sources. Implementations will be in the infrastructure layer.
"""

from .time_entry_repository import TimeEntryRepository
from .work_item_repository import WorkItemRepository
from .user_repository import UserRepository
from .report_repository import ReportRepository

__all__ = [
    "TimeEntryRepository",
    "WorkItemRepository",
    "UserRepository",
    "ReportRepository",
]