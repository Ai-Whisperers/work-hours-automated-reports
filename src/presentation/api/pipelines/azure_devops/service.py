"""Azure DevOps pipeline service."""

import logging
from typing import List

from .....infrastructure.config import get_settings
from .....infrastructure.api_clients import AzureDevOpsClient
from .....infrastructure.repositories import AzureDevOpsWorkItemRepository
from .schemas import WorkItemResponse, WorkItemBatchResponse


logger = logging.getLogger(__name__)


class AzureDevOpsService:
    """Service for Azure DevOps operations."""

    def __init__(self):
        """Initialize Azure DevOps service."""
        self.settings = get_settings()
        self.client = None
        self.repository = None

    async def initialize(self):
        """Initialize ADO client and repository."""
        if not self.client:
            self.client = AzureDevOpsClient(self.settings)
            self.repository = AzureDevOpsWorkItemRepository(self.client)

    async def close(self):
        """Close ADO client connection."""
        if self.client:
            await self.client.close()
            self.client = None
            self.repository = None

    async def test_connection(self) -> bool:
        """Test Azure DevOps connection.

        Returns:
            True if connection successful
        """
        await self.initialize()
        try:
            return await self.client.test_connection()
        except Exception as e:
            logger.error(f"ADO connection test failed: {e}")
            return False

    async def get_work_items(self, work_item_ids: List[int]) -> WorkItemBatchResponse:
        """Get work items by IDs.

        Args:
            work_item_ids: List of work item IDs

        Returns:
            Batch response with work items
        """
        await self.initialize()

        try:
            # Fetch work items from repository
            work_items = []
            for work_item_id in work_item_ids:
                try:
                    wi = await self.repository.get_by_id(work_item_id)
                    if wi:
                        work_items.append(
                            WorkItemResponse(
                                id=wi.id,
                                title=wi.title,
                                type=(
                                    wi.type.value
                                    if hasattr(wi.type, "value")
                                    else str(wi.type)
                                ),
                                state=(
                                    wi.state.value
                                    if hasattr(wi.state, "value")
                                    else str(wi.state)
                                ),
                                assigned_to=getattr(wi, "assigned_to", None),
                                created_date=(
                                    wi.created_date.isoformat()
                                    if wi.created_date
                                    else None
                                ),
                                changed_date=(
                                    wi.changed_date.isoformat()
                                    if wi.changed_date
                                    else None
                                ),
                            )
                        )
                except Exception as e:
                    logger.error(f"Failed to fetch work item {work_item_id}: {e}")
                    continue

            return WorkItemBatchResponse(work_items=work_items, count=len(work_items))

        except Exception as e:
            logger.error(f"Failed to get work items: {e}")
            raise
