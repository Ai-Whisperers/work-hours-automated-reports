"""Synchronous adapter for Clockify API client.

This adapter wraps the async ClockifyClient to provide a synchronous interface
for use in the activity tracker and commit tracker services.
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from .clockify_client import ClockifyClient


class ClockifySyncAdapter:
    """
    Synchronous wrapper around the async ClockifyClient.

    This adapter runs async methods in a new event loop to provide
    a synchronous interface for services that don't use async/await.
    """

    def __init__(self, settings=None):
        """
        Initialize the sync adapter.

        Args:
            settings: Optional settings override
        """
        self.client = ClockifyClient(settings)
        self._loop = None

    def _run_async(self, coro):
        """
        Run an async coroutine in a synchronous context.

        Args:
            coro: Coroutine to execute

        Returns:
            Result of the coroutine
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(coro)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def start_time_entry(
        self,
        description: str = "Work (auto)",
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Start a new time entry.

        Args:
            description: Entry description
            project_id: Optional project ID
            tags: Optional tag IDs

        Returns:
            Started time entry data
        """
        return self._run_async(
            self.client.start_time_entry(description, project_id, tags)
        )

    def stop_time_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Stop a running time entry.

        Args:
            entry_id: Time entry ID to stop

        Returns:
            Stopped time entry data
        """
        return self._run_async(self.client.stop_time_entry(entry_id))

    def create_time_entry_with_range(
        self,
        start: datetime,
        end: datetime,
        description: str,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a time entry with specific start and end times.

        Args:
            start: Start datetime
            end: End datetime
            description: Entry description
            project_id: Optional project ID
            tags: Optional tag IDs

        Returns:
            Created time entry data
        """
        return self._run_async(
            self.client.create_time_entry_with_range(
                start, end, description, project_id, tags
            )
        )

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current user information.

        Returns:
            User information dictionary
        """
        return self._run_async(self.client.get_current_user())

    def test_connection(self) -> bool:
        """
        Test API connection.

        Returns:
            True if connection is successful
        """
        return self._run_async(self.client.test_connection())

    def update_time_entry(
        self,
        entry_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing time entry.

        Args:
            entry_id: Time entry ID to update
            start: Optional new start datetime
            end: Optional new end datetime
            description: Optional new description
            project_id: Optional new project ID
            tags: Optional new tag IDs

        Returns:
            Updated time entry data
        """
        updates = {}

        if start is not None:
            updates["start"] = start.isoformat() + "Z"
        if end is not None:
            updates["end"] = end.isoformat() + "Z"
        if description is not None:
            updates["description"] = description
        if project_id is not None:
            updates["projectId"] = project_id
        if tags is not None:
            updates["tagIds"] = tags

        return self._run_async(self.client.update_time_entry(entry_id, updates))
