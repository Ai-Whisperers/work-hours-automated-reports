"""Azure DevOps pipeline schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class WorkItemQueryRequest(BaseModel):
    """Request model for querying work items."""

    work_item_ids: List[int] = Field(
        ...,
        description="List of work item IDs to query"
    )


class WorkItemResponse(BaseModel):
    """Response model for work item data."""

    id: int
    title: str
    type: str
    state: str
    assigned_to: Optional[str] = None
    created_date: Optional[str] = None
    changed_date: Optional[str] = None


class WorkItemBatchResponse(BaseModel):
    """Response model for batch work item query."""

    work_items: List[WorkItemResponse]
    count: int


class ADOConnectionRequest(BaseModel):
    """Request model for testing ADO connection."""

    organization: str = Field(..., description="Azure DevOps organization")
    project: str = Field(..., description="Azure DevOps project")
    pat: str = Field(..., description="Personal Access Token")


class ADOConnectionResponse(BaseModel):
    """Response model for ADO connection test."""

    connected: bool
    organization: str
    project: str
    message: Optional[str] = None
