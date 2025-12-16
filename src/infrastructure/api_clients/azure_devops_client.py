"""Azure DevOps API client implementation."""

import base64
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import logging

from .base_client import BaseAPIClient, NotFoundError
from ...domain.entities import WorkItem
from ...domain.value_objects import WorkItemId
from ...infrastructure.config import get_settings


logger = logging.getLogger(__name__)


class AzureDevOpsClient(BaseAPIClient):
    """Azure DevOps API client implementation.

    This client handles all interactions with the Azure DevOps API,
    including fetching work items, iterations, and running queries.
    """

    def __init__(self, settings=None):
        """Initialize Azure DevOps client.

        Args:
            settings: Optional settings override
        """
        settings = settings or get_settings()

        # Encode PAT for Basic Auth
        encoded_pat = base64.b64encode(f":{settings.ado_pat}".encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_pat}",
            "Content-Type": "application/json",
        }

        base_url = f"{settings.ado_base_url}/{settings.ado_organization}"

        super().__init__(
            base_url=base_url,
            headers=headers,
            timeout=settings.ado_timeout,
            max_retries=settings.ado_max_retries,
        )

        self.organization = settings.ado_organization
        self.project = settings.ado_project
        self.api_version = settings.ado_api_version
        self.batch_size = settings.ado_batch_size

    def _extract_items_from_response(
        self, response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract items from Azure DevOps API response.

        Args:
            response: API response

        Returns:
            List of items
        """
        # Azure DevOps returns items in 'value' property
        if isinstance(response, dict) and "value" in response:
            return response["value"]

        # For work item queries, items are in 'workItems'
        if isinstance(response, dict) and "workItems" in response:
            return response["workItems"]

        return []

    async def get_work_item(
        self, work_item_id: int, expand: Optional[str] = None
    ) -> Optional[WorkItem]:
        """Get a single work item by ID.

        Args:
            work_item_id: Work item ID
            expand: Optional expand parameter (Relations, Fields, etc.)

        Returns:
            WorkItem entity or None if not found
        """
        try:
            endpoint = f"/{self.project}/_apis/wit/workitems/{work_item_id}"

            params = {"api-version": self.api_version}
            if expand:
                params["$expand"] = expand

            data = await self.get(endpoint, params=params)
            return WorkItem.from_ado_data(data)

        except NotFoundError:
            logger.warning(f"Work item {work_item_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch work item {work_item_id}: {e}")
            return None

    async def get_work_items_batch(
        self,
        work_item_ids: Set[int],
        fields: Optional[List[str]] = None,
        expand: str = "None",
    ) -> List[WorkItem]:
        """Get multiple work items in batch.

        Args:
            work_item_ids: Set of work item IDs
            fields: Optional list of fields to return
            expand: Expand parameter

        Returns:
            List of WorkItem entities
        """
        if not work_item_ids:
            return []

        work_items = []
        ids_list = list(work_item_ids)

        # Process in batches (ADO limit is 200)
        for i in range(0, len(ids_list), self.batch_size):
            batch_ids = ids_list[i : i + self.batch_size]

            # Convert to comma-separated string
            ids_str = ",".join(map(str, batch_ids))

            endpoint = f"/{self.project}/_apis/wit/workitems"

            params = {
                "ids": ids_str,
                "api-version": self.api_version,
                "$expand": expand,
            }

            if fields:
                params["fields"] = ",".join(fields)

            try:
                response = await self.get(endpoint, params=params)
                items = self._extract_items_from_response(response)

                for item_data in items:
                    try:
                        work_item = WorkItem.from_ado_data(item_data)
                        work_items.append(work_item)
                    except Exception as e:
                        logger.warning(f"Failed to parse work item: {e}")
                        continue

            except Exception as e:
                logger.error(f"Failed to fetch batch of work items: {e}")
                continue

        return work_items

    async def query_work_items(self, wiql: str, top: Optional[int] = None) -> List[int]:
        """Execute a WIQL query and return work item IDs.

        Args:
            wiql: Work Item Query Language query
            top: Maximum number of results

        Returns:
            List of work item IDs
        """
        endpoint = f"/{self.project}/_apis/wit/wiql"

        body = {"query": wiql}
        if top:
            body["$top"] = top

        params = {"api-version": self.api_version}

        response = await self.post(endpoint, json_data=body, params=params)

        # Extract work item IDs from response
        work_items = response.get("workItems", [])
        return [item["id"] for item in work_items]

    async def get_work_items_by_query(
        self, wiql: str, fields: Optional[List[str]] = None
    ) -> List[WorkItem]:
        """Execute WIQL query and fetch full work items.

        Args:
            wiql: Work Item Query Language query
            fields: Optional list of fields to return

        Returns:
            List of WorkItem entities
        """
        # First, get IDs from query
        work_item_ids = await self.query_work_items(wiql)

        # Then fetch full work items
        if work_item_ids:
            return await self.get_work_items_batch(set(work_item_ids), fields=fields)

        return []

    async def get_iterations(self, team: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team iterations.

        Args:
            team: Optional team name

        Returns:
            List of iteration dictionaries
        """
        if team:
            endpoint = f"/{self.project}/{team}/_apis/work/teamsettings/iterations"
        else:
            endpoint = f"/{self.project}/_apis/work/teamsettings/iterations"

        params = {"api-version": self.api_version}

        response = await self.get(endpoint, params=params)
        return self._extract_items_from_response(response)

    async def get_current_iteration(
        self, team: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the current iteration.

        Args:
            team: Optional team name

        Returns:
            Current iteration dictionary or None
        """
        iterations = await self.get_iterations(team)

        now = datetime.now()

        for iteration in iterations:
            attributes = iteration.get("attributes", {})
            start_date = attributes.get("startDate")
            end_date = attributes.get("finishDate")

            if start_date and end_date:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if start <= now <= end:
                    return iteration

        return None

    async def get_areas(self, depth: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get area paths.

        Args:
            depth: Optional depth of area tree

        Returns:
            List of area dictionaries
        """
        endpoint = f"/{self.project}/_apis/wit/classificationnodes/areas"

        params = {"api-version": self.api_version}
        if depth:
            params["$depth"] = depth

        return await self.get(endpoint, params=params)

    async def get_work_items_in_iteration(
        self,
        iteration_path: str,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
    ) -> List[WorkItem]:
        """Get work items in a specific iteration.

        Args:
            iteration_path: Iteration path
            work_item_types: Optional filter by types
            states: Optional filter by states

        Returns:
            List of WorkItem entities
        """
        # Build WIQL query
        wiql = f"""
        SELECT [System.Id], [System.Title], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.project}'
          AND [System.IterationPath] = '{iteration_path}'
        """

        if work_item_types:
            types_str = "', '".join(work_item_types)
            wiql += f" AND [System.WorkItemType] IN ('{types_str}')"

        if states:
            states_str = "', '".join(states)
            wiql += f" AND [System.State] IN ('{states_str}')"

        wiql += " ORDER BY [Microsoft.VSTS.Common.Priority] ASC"

        return await self.get_work_items_by_query(wiql)

    async def get_work_items_by_ids(
        self, work_item_ids: Set[WorkItemId]
    ) -> List[WorkItem]:
        """Get work items by WorkItemId value objects.

        Args:
            work_item_ids: Set of WorkItemId value objects

        Returns:
            List of WorkItem entities
        """
        # Convert WorkItemId objects to integers
        int_ids = {int(wi_id) for wi_id in work_item_ids}
        return await self.get_work_items_batch(int_ids)

    async def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent_id: Optional[int] = None,
    ) -> WorkItem:
        """Create a new work item.

        Args:
            work_item_type: Type of work item
            title: Work item title
            description: Optional description
            assigned_to: Optional assignee
            area_path: Optional area path
            iteration_path: Optional iteration path
            tags: Optional tags
            parent_id: Optional parent work item ID

        Returns:
            Created WorkItem entity
        """
        endpoint = f"/{self.project}/_apis/wit/workitems/${work_item_type}"

        # Build patch document
        operations = [{"op": "add", "path": "/fields/System.Title", "value": title}]

        if description:
            operations.append(
                {
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": description,
                }
            )

        if assigned_to:
            operations.append(
                {"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to}
            )

        if area_path:
            operations.append(
                {"op": "add", "path": "/fields/System.AreaPath", "value": area_path}
            )

        if iteration_path:
            operations.append(
                {
                    "op": "add",
                    "path": "/fields/System.IterationPath",
                    "value": iteration_path,
                }
            )

        if tags:
            operations.append(
                {"op": "add", "path": "/fields/System.Tags", "value": "; ".join(tags)}
            )

        if parent_id:
            operations.append(
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.base_url}/{self.project}/_apis/wit/workItems/{parent_id}",
                    },
                }
            )

        params = {"api-version": self.api_version}

        # Use PATCH with application/json-patch+json content type
        headers = {"Content-Type": "application/json-patch+json"}

        response = await self.client.patch(
            f"{self.base_url}{endpoint}",
            json=operations,
            params=params,
            headers={**self.headers, **headers},
        )

        return WorkItem.from_ado_data(response.json())

    async def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection is successful
        """
        try:
            endpoint = f"/{self.project}/_apis/wit/workitems"
            params = {
                "ids": "1",  # Try to fetch work item 1
                "api-version": self.api_version,
            }

            await self.get(endpoint, params=params)
            logger.info(f"Connected to Azure DevOps project: {self.project}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Azure DevOps: {e}")
            return False
