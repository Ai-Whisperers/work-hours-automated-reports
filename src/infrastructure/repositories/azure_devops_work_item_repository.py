"""Azure DevOps implementation of WorkItemRepository."""

from typing import List, Optional, Set
import logging

from ...domain.repositories import WorkItemRepository
from ...domain.entities import WorkItem
from ...domain.entities.work_item import WorkItemState, WorkItemType
from ...domain.value_objects import WorkItemId
from ..api_clients import AzureDevOpsClient

logger = logging.getLogger(__name__)


class AzureDevOpsWorkItemRepository(WorkItemRepository):
    """Repository implementation for Azure DevOps work items.

    This adapter implements the WorkItemRepository port using
    the Azure DevOps API client.
    """

    def __init__(self, ado_client: AzureDevOpsClient):
        """Initialize repository with Azure DevOps client.

        Args:
            ado_client: Azure DevOps API client
        """
        self.client = ado_client

    async def get_by_id(self, work_item_id: WorkItemId) -> Optional[WorkItem]:
        """Get a work item by its ID.

        Args:
            work_item_id: The work item ID

        Returns:
            WorkItem if found, None otherwise
        """
        return await self.client.get_work_item(int(work_item_id))

    async def get_by_ids(self, work_item_ids: Set[WorkItemId]) -> List[WorkItem]:
        """Get multiple work items by their IDs.

        Args:
            work_item_ids: Set of work item IDs

        Returns:
            List of found work items
        """
        return await self.client.get_work_items_by_ids(work_item_ids)

    async def get_by_iteration(
        self, iteration_path: str, states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items in a specific iteration.

        Args:
            iteration_path: The iteration path
            states: Optional filter by states

        Returns:
            List of work items in the iteration
        """
        state_strings = None
        if states:
            state_strings = [state.value for state in states]

        return await self.client.get_work_items_in_iteration(
            iteration_path=iteration_path, states=state_strings
        )

    async def get_by_area(
        self, area_path: str, states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items in a specific area.

        Args:
            area_path: The area path
            states: Optional filter by states

        Returns:
            List of work items in the area
        """
        # Build WIQL query
        wiql = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.client.project}'
          AND [System.AreaPath] UNDER '{area_path}'
        """

        if states:
            states_str = "', '".join([s.value for s in states])
            wiql += f" AND [System.State] IN ('{states_str}')"

        return await self.client.get_work_items_by_query(wiql)

    async def get_by_assigned_to(
        self, assigned_to: str, states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items assigned to a specific person.

        Args:
            assigned_to: The person's name or email
            states: Optional filter by states

        Returns:
            List of work items assigned to the person
        """
        # Build WIQL query
        wiql = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.client.project}'
          AND [System.AssignedTo] = '{assigned_to}'
        """

        if states:
            states_str = "', '".join([s.value for s in states])
            wiql += f" AND [System.State] IN ('{states_str}')"

        wiql += " ORDER BY [System.ChangedDate] DESC"

        return await self.client.get_work_items_by_query(wiql)

    async def get_by_type(
        self, work_item_type: WorkItemType, states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items of a specific type.

        Args:
            work_item_type: The work item type
            states: Optional filter by states

        Returns:
            List of work items of the specified type
        """
        # Build WIQL query
        wiql = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.client.project}'
          AND [System.WorkItemType] = '{work_item_type.value}'
        """

        if states:
            states_str = "', '".join([s.value for s in states])
            wiql += f" AND [System.State] IN ('{states_str}')"

        return await self.client.get_work_items_by_query(wiql)

    async def search_by_title(
        self, title_pattern: str, states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Search work items by title pattern.

        Args:
            title_pattern: Pattern to search in titles
            states: Optional filter by states

        Returns:
            List of work items matching the pattern
        """
        # Build WIQL query with CONTAINS for title search
        wiql = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.client.project}'
          AND [System.Title] CONTAINS '{title_pattern}'
        """

        if states:
            states_str = "', '".join([s.value for s in states])
            wiql += f" AND [System.State] IN ('{states_str}')"

        return await self.client.get_work_items_by_query(wiql)

    async def get_children(self, parent_id: WorkItemId) -> List[WorkItem]:
        """Get child work items of a parent.

        Args:
            parent_id: The parent work item ID

        Returns:
            List of child work items
        """
        # Build WIQL query for children
        wiql = f"""
        SELECT [System.Id]
        FROM WorkItemLinks
        WHERE [Source].[System.Id] = {int(parent_id)}
          AND [System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward'
        MODE (Recursive)
        """

        return await self.client.get_work_items_by_query(wiql)

    async def save(self, work_item: WorkItem) -> WorkItem:
        """Save a work item.

        Args:
            work_item: The work item to save

        Returns:
            The saved work item
        """
        # Create new work item
        return await self.client.create_work_item(
            work_item_type=work_item.work_item_type.value,
            title=work_item.title,
            assigned_to=work_item.assigned_to,
            area_path=work_item.area_path,
            iteration_path=work_item.iteration_path,
            tags=work_item.tags,
            parent_id=int(work_item.parent_id) if work_item.parent_id else None,
        )

    async def save_batch(self, work_items: List[WorkItem]) -> List[WorkItem]:
        """Save multiple work items.

        Args:
            work_items: List of work items to save

        Returns:
            List of saved work items
        """
        saved_items = []

        for item in work_items:
            try:
                saved_item = await self.save(item)
                saved_items.append(saved_item)
            except Exception as e:
                logger.error(f"Failed to save work item: {e}")
                continue

        return saved_items

    async def query(self, wiql: str) -> List[WorkItem]:
        """Execute a WIQL query.

        Args:
            wiql: Work Item Query Language query

        Returns:
            List of work items matching the query
        """
        return await self.client.get_work_items_by_query(wiql)
