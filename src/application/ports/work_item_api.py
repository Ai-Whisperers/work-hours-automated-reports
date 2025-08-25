"""Work item API port."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Set

from ...domain.entities import WorkItem
from ...domain.value_objects import WorkItemId


class WorkItemAPI(ABC):
    """Port for work item API services.
    
    This interface abstracts work item management functionality,
    allowing different implementations (Azure DevOps, Jira, etc.).
    """
    
    @abstractmethod
    async def get_work_item(self, work_item_id: WorkItemId) -> Optional[WorkItem]:
        """Get a single work item by ID.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            WorkItem if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_work_items_batch(
        self,
        work_item_ids: Set[WorkItemId],
        fields: Optional[List[str]] = None
    ) -> List[WorkItem]:
        """Get multiple work items in batch.
        
        Args:
            work_item_ids: Set of work item IDs
            fields: Optional list of fields to return
            
        Returns:
            List of work items
        """
        pass
    
    @abstractmethod
    async def query_work_items(self, query: str) -> List[WorkItem]:
        """Execute a query to get work items.
        
        Args:
            query: Query string (WIQL for Azure DevOps, JQL for Jira, etc.)
            
        Returns:
            List of work items matching the query
        """
        pass
    
    @abstractmethod
    async def get_iterations(self, team: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get iterations/sprints.
        
        Args:
            team: Optional team filter
            
        Returns:
            List of iteration dictionaries
        """
        pass
    
    @abstractmethod
    async def get_current_iteration(self, team: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the current active iteration.
        
        Args:
            team: Optional team filter
            
        Returns:
            Current iteration dictionary or None
        """
        pass
    
    @abstractmethod
    async def get_areas(self) -> List[Dict[str, Any]]:
        """Get area paths.
        
        Returns:
            List of area dictionaries
        """
        pass
    
    @abstractmethod
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
        custom_fields: Optional[Dict[str, Any]] = None
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
            custom_fields: Optional custom fields
            
        Returns:
            Created work item
        """
        pass
    
    @abstractmethod
    async def update_work_item(
        self,
        work_item_id: WorkItemId,
        updates: Dict[str, Any]
    ) -> WorkItem:
        """Update an existing work item.
        
        Args:
            work_item_id: Work item ID
            updates: Fields to update
            
        Returns:
            Updated work item
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connection.
        
        Returns:
            True if connection is successful
        """
        pass