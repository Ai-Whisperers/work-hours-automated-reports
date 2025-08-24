"""Work item repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from ..entities import WorkItem
from ..entities.work_item import WorkItemState, WorkItemType
from ..value_objects import WorkItemId


class WorkItemRepository(ABC):
    """Abstract repository for work items.
    
    This is a port in hexagonal architecture that defines how
    the domain interacts with work item data storage.
    """
    
    @abstractmethod
    async def get_by_id(self, work_item_id: WorkItemId) -> Optional[WorkItem]:
        """Get a work item by its ID.
        
        Args:
            work_item_id: The work item ID
            
        Returns:
            WorkItem if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_ids(self, work_item_ids: Set[WorkItemId]) -> List[WorkItem]:
        """Get multiple work items by their IDs.
        
        Args:
            work_item_ids: Set of work item IDs
            
        Returns:
            List of found work items
        """
        pass
    
    @abstractmethod
    async def get_by_iteration(
        self,
        iteration_path: str,
        states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items in a specific iteration.
        
        Args:
            iteration_path: The iteration path
            states: Optional filter by states
            
        Returns:
            List of work items in the iteration
        """
        pass
    
    @abstractmethod
    async def get_by_area(
        self,
        area_path: str,
        states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items in a specific area.
        
        Args:
            area_path: The area path
            states: Optional filter by states
            
        Returns:
            List of work items in the area
        """
        pass
    
    @abstractmethod
    async def get_by_assigned_to(
        self,
        assigned_to: str,
        states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items assigned to a specific person.
        
        Args:
            assigned_to: The person's name or email
            states: Optional filter by states
            
        Returns:
            List of work items assigned to the person
        """
        pass
    
    @abstractmethod
    async def get_by_type(
        self,
        work_item_type: WorkItemType,
        states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Get work items of a specific type.
        
        Args:
            work_item_type: The work item type
            states: Optional filter by states
            
        Returns:
            List of work items of the specified type
        """
        pass
    
    @abstractmethod
    async def search_by_title(
        self,
        title_pattern: str,
        states: Optional[List[WorkItemState]] = None
    ) -> List[WorkItem]:
        """Search work items by title pattern.
        
        Args:
            title_pattern: Pattern to search in titles
            states: Optional filter by states
            
        Returns:
            List of work items matching the pattern
        """
        pass
    
    @abstractmethod
    async def get_children(self, parent_id: WorkItemId) -> List[WorkItem]:
        """Get child work items of a parent.
        
        Args:
            parent_id: The parent work item ID
            
        Returns:
            List of child work items
        """
        pass
    
    @abstractmethod
    async def save(self, work_item: WorkItem) -> WorkItem:
        """Save a work item.
        
        Args:
            work_item: The work item to save
            
        Returns:
            The saved work item
        """
        pass
    
    @abstractmethod
    async def save_batch(self, work_items: List[WorkItem]) -> List[WorkItem]:
        """Save multiple work items.
        
        Args:
            work_items: List of work items to save
            
        Returns:
            List of saved work items
        """
        pass
    
    @abstractmethod
    async def query(self, wiql: str) -> List[WorkItem]:
        """Execute a WIQL query.
        
        Args:
            wiql: Work Item Query Language query
            
        Returns:
            List of work items matching the query
        """
        pass