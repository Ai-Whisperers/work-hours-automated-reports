"""Time entry repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import TimeEntry
from ..value_objects import DateRange


class TimeEntryRepository(ABC):
    """Abstract repository for time entries.

    This is a port in hexagonal architecture that defines how
    the domain interacts with time entry data storage.
    """

    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[TimeEntry]:
        """Get a time entry by its ID.

        Args:
            entry_id: The time entry ID

        Returns:
            TimeEntry if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        date_range: DateRange,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[TimeEntry]:
        """Get time entries within a date range.

        Args:
            date_range: The date range to search
            user_id: Optional filter by user ID
            project_id: Optional filter by project ID

        Returns:
            List of time entries matching the criteria
        """
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: str, date_range: Optional[DateRange] = None
    ) -> List[TimeEntry]:
        """Get all time entries for a specific user.

        Args:
            user_id: The user ID
            date_range: Optional date range filter

        Returns:
            List of time entries for the user
        """
        pass

    @abstractmethod
    async def get_by_project(
        self, project_id: str, date_range: Optional[DateRange] = None
    ) -> List[TimeEntry]:
        """Get all time entries for a specific project.

        Args:
            project_id: The project ID
            date_range: Optional date range filter

        Returns:
            List of time entries for the project
        """
        pass

    @abstractmethod
    async def get_unmatched_entries(self, date_range: DateRange) -> List[TimeEntry]:
        """Get time entries that haven't been matched to work items.

        Args:
            date_range: The date range to search

        Returns:
            List of unmatched time entries
        """
        pass

    @abstractmethod
    async def save(self, time_entry: TimeEntry) -> TimeEntry:
        """Save a time entry.

        Args:
            time_entry: The time entry to save

        Returns:
            The saved time entry
        """
        pass

    @abstractmethod
    async def save_batch(self, time_entries: List[TimeEntry]) -> List[TimeEntry]:
        """Save multiple time entries.

        Args:
            time_entries: List of time entries to save

        Returns:
            List of saved time entries
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a time entry.

        Args:
            entry_id: The time entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass
