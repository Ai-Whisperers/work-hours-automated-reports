"""Clockify API client implementation."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .base_client import BaseAPIClient
from ...domain.entities import TimeEntry
from ...domain.value_objects import DateRange
from ...infrastructure.config import get_settings


logger = logging.getLogger(__name__)


class ClockifyClient(BaseAPIClient):
    """Clockify API client implementation.
    
    This client handles all interactions with the Clockify API,
    including fetching time entries, users, and projects.
    """
    
    def __init__(self, settings=None):
        """Initialize Clockify client.
        
        Args:
            settings: Optional settings override
        """
        settings = settings or get_settings()
        
        headers = {
            "X-Api-Key": settings.clockify_api_key,
            "Content-Type": "application/json"
        }
        
        super().__init__(
            base_url=settings.clockify_base_url,
            headers=headers,
            timeout=settings.clockify_timeout,
            max_retries=settings.clockify_max_retries
        )
        
        self.workspace_id = settings.clockify_workspace_id
    
    def _extract_items_from_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract items from Clockify API response.
        
        Args:
            response: API response
            
        Returns:
            List of items
        """
        # Clockify returns array directly for most endpoints
        if isinstance(response, list):
            return response
        
        # Some endpoints return object with data property
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        
        return []
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user information.
        
        Returns:
            User information dictionary
        """
        return await self.get("/user")
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users in workspace.
        
        Returns:
            List of user dictionaries
        """
        endpoint = f"/workspaces/{self.workspace_id}/users"
        return await self.get(endpoint)
    
    async def get_projects(self, archived: bool = False) -> List[Dict[str, Any]]:
        """Get all projects in workspace.
        
        Args:
            archived: Include archived projects
            
        Returns:
            List of project dictionaries
        """
        endpoint = f"/workspaces/{self.workspace_id}/projects"
        params = {"archived": str(archived).lower()}
        return await self.get(endpoint, params=params)
    
    async def get_time_entries(
        self,
        user_id: str,
        date_range: DateRange,
        project_id: Optional[str] = None,
        in_progress: bool = False
    ) -> List[TimeEntry]:
        """Get time entries for a user.
        
        Args:
            user_id: User ID
            date_range: Date range for entries
            project_id: Optional project filter
            in_progress: Include in-progress entries
            
        Returns:
            List of TimeEntry entities
        """
        endpoint = f"/workspaces/{self.workspace_id}/user/{user_id}/time-entries"
        
        # Format dates for API
        start_str, end_str = date_range.format_for_api()
        
        params = {
            "start": start_str,
            "end": end_str,
            "in-progress": str(in_progress).lower()
        }
        
        if project_id:
            params["project"] = project_id
        
        # Use pagination to get all entries
        all_entries = await self.get_paginated(
            endpoint,
            params=params,
            page_size=100
        )
        
        # Convert to domain entities
        time_entries = []
        for entry_data in all_entries:
            try:
                # Add user name if not present
                if "userName" not in entry_data:
                    entry_data["userName"] = await self._get_user_name(user_id)
                
                time_entry = TimeEntry.from_clockify_data(entry_data)
                time_entries.append(time_entry)
            except Exception as e:
                logger.warning(f"Failed to parse time entry: {e}")
                continue
        
        return time_entries
    
    async def get_time_entries_for_all_users(
        self,
        date_range: DateRange,
        project_id: Optional[str] = None
    ) -> List[TimeEntry]:
        """Get time entries for all users in workspace.
        
        Args:
            date_range: Date range for entries
            project_id: Optional project filter
            
        Returns:
            List of TimeEntry entities
        """
        # Get all users
        users = await self.get_users()
        
        # Fetch entries for each user concurrently
        import asyncio
        
        tasks = [
            self.get_time_entries(
                user["id"],
                date_range,
                project_id
            )
            for user in users
        ]
        
        user_entries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all entries
        all_entries = []
        for entries in user_entries:
            if isinstance(entries, Exception):
                logger.error(f"Failed to fetch entries for user: {entries}")
                continue
            all_entries.extend(entries)
        
        return all_entries
    
    async def get_detailed_report(
        self,
        date_range: DateRange,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed report from Clockify.
        
        Args:
            date_range: Date range for report
            group_by: Grouping option (project, user, date, etc.)
            
        Returns:
            Report data dictionary
        """
        endpoint = f"/workspaces/{self.workspace_id}/reports/detailed"
        
        start_str, end_str = date_range.format_for_api()
        
        body = {
            "dateRangeStart": start_str,
            "dateRangeEnd": end_str,
            "detailedFilter": {
                "page": 1,
                "pageSize": 1000,
                "sortColumn": "DATE"
            }
        }
        
        if group_by:
            body["groupBy"] = group_by.upper()
        
        return await self.post(endpoint, json_data=body)
    
    async def get_summary_report(
        self,
        date_range: DateRange,
        group_by: str = "PROJECT"
    ) -> Dict[str, Any]:
        """Get summary report from Clockify.
        
        Args:
            date_range: Date range for report
            group_by: Grouping option
            
        Returns:
            Summary report data
        """
        endpoint = f"/workspaces/{self.workspace_id}/reports/summary"
        
        start_str, end_str = date_range.format_for_api()
        
        body = {
            "dateRangeStart": start_str,
            "dateRangeEnd": end_str,
            "groupBy": group_by.upper(),
            "summaryFilter": {
                "groups": [group_by.upper()]
            }
        }
        
        return await self.post(endpoint, json_data=body)
    
    async def create_time_entry(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        description: str,
        project_id: Optional[str] = None,
        billable: bool = True,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new time entry.
        
        Args:
            user_id: User ID
            start: Start time
            end: End time
            description: Entry description
            project_id: Optional project ID
            billable: Whether entry is billable
            tags: Optional tags
            
        Returns:
            Created time entry data
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries"
        
        body = {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "description": description,
            "billable": billable,
            "projectId": project_id,
            "tagIds": tags or []
        }
        
        return await self.post(endpoint, json_data=body)
    
    async def update_time_entry(
        self,
        entry_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing time entry.
        
        Args:
            entry_id: Time entry ID
            updates: Fields to update
            
        Returns:
            Updated time entry data
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries/{entry_id}"
        return await self.put(endpoint, json_data=updates)
    
    async def delete_time_entry(self, entry_id: str) -> bool:
        """Delete a time entry.
        
        Args:
            entry_id: Time entry ID
            
        Returns:
            True if deleted successfully
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries/{entry_id}"
        return await self.delete(endpoint)
    
    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags in workspace.
        
        Returns:
            List of tag dictionaries
        """
        endpoint = f"/workspaces/{self.workspace_id}/tags"
        return await self.get(endpoint)
    
    async def _get_user_name(self, user_id: str) -> str:
        """Get user name by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User name or "Unknown"
        """
        try:
            users = await self.get_users()
            for user in users:
                if user["id"] == user_id:
                    return user.get("name", "Unknown")
        except Exception as e:
            logger.error(f"Failed to get user name: {e}")
        
        return "Unknown"
    
    async def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection is successful
        """
        try:
            user = await self.get_current_user()
            logger.info(f"Connected to Clockify as: {user.get('name', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Clockify: {e}")
            return False

    async def start_time_entry(
        self,
        description: str = "Work (auto)",
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Start a new time entry (timer).

        Args:
            description: Entry description
            project_id: Optional project ID
            tags: Optional tag IDs

        Returns:
            Started time entry data
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries"

        body = {
            "start": datetime.utcnow().isoformat() + "Z",
            "description": description
        }

        if project_id:
            body["projectId"] = project_id

        if tags:
            body["tagIds"] = tags

        return await self.post(endpoint, json_data=body)

    async def stop_time_entry(self, entry_id: str) -> Dict[str, Any]:
        """Stop a running time entry.

        Args:
            entry_id: Time entry ID to stop

        Returns:
            Stopped time entry data
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries/{entry_id}"

        body = {
            "end": datetime.utcnow().isoformat() + "Z"
        }

        return await self.patch(endpoint, json_data=body)

    async def create_time_entry_with_range(
        self,
        start: datetime,
        end: datetime,
        description: str,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a time entry with specific start and end times.

        Args:
            start: Start datetime
            end: End datetime
            description: Entry description
            project_id: Optional project ID
            tags: Optional tag IDs

        Returns:
            Created time entry data
        """
        endpoint = f"/workspaces/{self.workspace_id}/time-entries"

        body = {
            "start": start.isoformat() + "Z" if not start.isoformat().endswith("Z") else start.isoformat(),
            "end": end.isoformat() + "Z" if not end.isoformat().endswith("Z") else end.isoformat(),
            "description": description
        }

        if project_id:
            body["projectId"] = project_id

        if tags:
            body["tagIds"] = tags

        return await self.post(endpoint, json_data=body)