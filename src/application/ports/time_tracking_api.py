"""Time tracking API port."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from ...domain.entities import TimeEntry
from ...domain.value_objects import DateRange


class TimeTrackingAPI(ABC):
    """Port for time tracking API services.

    This interface abstracts time tracking functionality,
    allowing different implementations (Clockify, Toggl, etc.).
    """

    @abstractmethod
    async def get_time_entries(
        self,
        date_range: DateRange,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[TimeEntry]:
        """Get time entries for a date range.

        Args:
            date_range: Date range to fetch entries for
            user_id: Optional user ID filter
            project_id: Optional project ID filter

        Returns:
            List of time entries
        """
        pass

    @abstractmethod
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users in the workspace.

        Returns:
            List of user dictionaries
        """
        pass

    @abstractmethod
    async def get_projects(
        self, include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all projects in the workspace.

        Args:
            include_archived: Include archived projects

        Returns:
            List of project dictionaries
        """
        pass

    @abstractmethod
    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags in the workspace.

        Returns:
            List of tag dictionaries
        """
        pass

    @abstractmethod
    async def create_time_entry(
        self,
        start: datetime,
        end: datetime,
        description: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        billable: bool = True,
        tags: Optional[List[str]] = None,
    ) -> TimeEntry:
        """Create a new time entry.

        Args:
            start: Start time
            end: End time
            description: Entry description
            project_id: Optional project ID
            user_id: Optional user ID
            billable: Whether entry is billable
            tags: Optional tags

        Returns:
            Created time entry
        """
        pass

    @abstractmethod
    async def update_time_entry(
        self, entry_id: str, updates: Dict[str, Any]
    ) -> TimeEntry:
        """Update an existing time entry.

        Args:
            entry_id: Time entry ID
            updates: Fields to update

        Returns:
            Updated time entry
        """
        pass

    @abstractmethod
    async def delete_time_entry(self, entry_id: str) -> bool:
        """Delete a time entry.

        Args:
            entry_id: Time entry ID

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection is successful
        """
        pass
