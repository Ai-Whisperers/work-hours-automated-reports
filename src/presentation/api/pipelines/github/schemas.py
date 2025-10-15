"""GitHub pipeline schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class GitHubIssueRequest(BaseModel):
    """Request model for GitHub issue query."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_numbers: List[int] = Field(..., description="List of issue numbers")


class GitHubIssueResponse(BaseModel):
    """Response model for GitHub issue."""

    number: int
    title: str
    state: str
    assignee: Optional[str] = None
    created_at: str
    updated_at: str
    labels: List[str] = []


class GitHubBatchResponse(BaseModel):
    """Response model for batch GitHub issue query."""

    issues: List[GitHubIssueResponse]
    count: int


class GitHubConnectionRequest(BaseModel):
    """Request model for testing GitHub connection."""

    token: Optional[str] = Field(None, description="GitHub Personal Access Token")


class GitHubConnectionResponse(BaseModel):
    """Response model for GitHub connection test."""

    connected: bool
    rate_limit_remaining: Optional[int] = None
    message: Optional[str] = None
