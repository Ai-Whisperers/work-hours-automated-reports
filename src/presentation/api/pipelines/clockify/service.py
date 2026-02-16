"""Clockify pipeline service."""

import logging
from datetime import datetime
from typing import List, Optional

from .....infrastructure.config import get_settings
from .....infrastructure.api_clients import ClockifyClient
from .....infrastructure.repositories import ClockifyTimeEntryRepository
from .....domain.value_objects import DateRange
from .schemas import TimeEntryResponse, TimeEntryBatchResponse

logger = logging.getLogger(__name__)


class ClockifyService:
    """Service for Clockify operations."""

    def __init__(self):
        """Initialize Clockify service."""
        self.settings = get_settings()
        self.client = None
        self.repository = None

    async def initialize(self):
        """Initialize Clockify client and repository."""
        if not self.client:
            self.client = ClockifyClient(self.settings)
            self.repository = ClockifyTimeEntryRepository(self.client)

    async def close(self):
        """Close Clockify client connection."""
        if self.client:
            await self.client.close()
            self.client = None
            self.repository = None

    async def test_connection(self) -> bool:
        """Test Clockify connection.

        Returns:
            True if connection successful
        """
        await self.initialize()
        try:
            return await self.client.test_connection()
        except Exception as e:
            logger.error(f"Clockify connection test failed: {e}")
            return False

    async def get_time_entries(
        self,
        start_date: str,
        end_date: str,
        user_ids: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None,
    ) -> TimeEntryBatchResponse:
        """Get time entries for a date range.

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            user_ids: Optional list of user IDs to filter
            project_ids: Optional list of project IDs to filter

        Returns:
            Batch response with time entries
        """
        await self.initialize()

        try:
            # Parse dates
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            date_range = DateRange(start, end)

            # Fetch time entries
            entries = await self.repository.get_by_date_range(
                date_range, user_ids=user_ids, project_ids=project_ids
            )

            # Convert to response models
            time_entries = []
            total_hours = 0.0

            for entry in entries:
                duration_hours = entry.duration.total_seconds() / 3600
                total_hours += duration_hours

                time_entries.append(
                    TimeEntryResponse(
                        id=entry.id,
                        description=entry.description,
                        start=entry.start_time.isoformat(),
                        end=entry.end_time.isoformat() if entry.end_time else None,
                        duration_hours=round(duration_hours, 2),
                        user_id=entry.user_id,
                        user_name=entry.user_name,
                        project_id=getattr(entry, "project_id", None),
                        project_name=getattr(entry, "project_name", None),
                    )
                )

            return TimeEntryBatchResponse(
                time_entries=time_entries,
                count=len(time_entries),
                total_hours=round(total_hours, 2),
            )

        except Exception as e:
            logger.error(f"Failed to get time entries: {e}")
            raise
