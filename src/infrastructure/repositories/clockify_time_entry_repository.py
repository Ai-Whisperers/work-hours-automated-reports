"""Clockify implementation of TimeEntryRepository."""

from typing import List, Optional
import logging

from ...domain.repositories import TimeEntryRepository
from ...domain.entities import TimeEntry
from ...domain.value_objects import DateRange
from ..api_clients import ClockifyClient

logger = logging.getLogger(__name__)


class ClockifyTimeEntryRepository(TimeEntryRepository):
    """Repository implementation for Clockify time entries.

    This adapter implements the TimeEntryRepository port using
    the Clockify API client.
    """

    def __init__(self, clockify_client: ClockifyClient):
        """Initialize repository with Clockify client.

        Args:
            clockify_client: Clockify API client
        """
        self.client = clockify_client

    async def get_by_id(self, entry_id: str) -> Optional[TimeEntry]:
        """Get a time entry by its ID.

        Args:
            entry_id: The time entry ID

        Returns:
            TimeEntry if found, None otherwise
        """
        # Clockify doesn't have a direct endpoint for single entry
        # Would need to fetch user's entries and filter
        logger.warning("get_by_id not fully implemented for Clockify")
        return None

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
        if user_id:
            # Get entries for specific user
            return await self.client.get_time_entries(
                user_id=user_id, date_range=date_range, project_id=project_id
            )
        else:
            # Get entries for all users
            return await self.client.get_time_entries_for_all_users(
                date_range=date_range, project_id=project_id
            )

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
        if not date_range:
            # Default to last 30 days if no range specified
            date_range = DateRange.last_n_days(30)

        return await self.client.get_time_entries(
            user_id=user_id, date_range=date_range
        )

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
        if not date_range:
            # Default to last 30 days if no range specified
            date_range = DateRange.last_n_days(30)

        return await self.client.get_time_entries_for_all_users(
            date_range=date_range, project_id=project_id
        )

    async def get_unmatched_entries(self, date_range: DateRange) -> List[TimeEntry]:
        """Get time entries that haven't been matched to work items.

        Args:
            date_range: The date range to search

        Returns:
            List of unmatched time entries
        """
        all_entries = await self.get_by_date_range(date_range)

        # Filter entries without work item IDs in description
        unmatched = []
        for entry in all_entries:
            if not entry.is_matched:
                unmatched.append(entry)

        return unmatched

    async def save(self, time_entry: TimeEntry) -> TimeEntry:
        """Save a time entry.

        Args:
            time_entry: The time entry to save

        Returns:
            The saved time entry
        """
        # Convert to Clockify format and save
        result = await self.client.create_time_entry(
            user_id=time_entry.user_id,
            start=time_entry.start_time,
            end=time_entry.end_time,
            description=time_entry.description or "",
            project_id=time_entry.project_id,
            billable=time_entry.billable,
            tags=time_entry.tags,
        )

        # Convert back to domain entity
        return TimeEntry.from_clockify_data(result)

    async def save_batch(self, time_entries: List[TimeEntry]) -> List[TimeEntry]:
        """Save multiple time entries.

        Args:
            time_entries: List of time entries to save

        Returns:
            List of saved time entries
        """
        saved_entries = []

        for entry in time_entries:
            try:
                saved_entry = await self.save(entry)
                saved_entries.append(saved_entry)
            except Exception as e:
                logger.error(f"Failed to save time entry: {e}")
                continue

        return saved_entries

    async def delete(self, entry_id: str) -> bool:
        """Delete a time entry.

        Args:
            entry_id: The time entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.client.delete_time_entry(entry_id)
