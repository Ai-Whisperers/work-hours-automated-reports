"""Domain entities.

Entities are domain objects that have a distinct identity that runs
through time and different states.
"""

from .time_entry import TimeEntry
from .work_item import WorkItem

__all__ = [
    "TimeEntry",
    "WorkItem",
]