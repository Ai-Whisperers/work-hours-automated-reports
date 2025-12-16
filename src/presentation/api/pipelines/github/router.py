"""GitHub pipeline router."""

import logging
from fastapi import APIRouter

from .schemas import (
    GitHubIssueRequest,
    GitHubIssueResponse,
    GitHubBatchResponse,
    GitHubConnectionRequest,
    GitHubConnectionResponse,
)
from .service import GitHubService


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/connection", response_model=GitHubConnectionResponse)
async def check_connection(request: GitHubConnectionRequest):
    """Check GitHub connection status.

    Args:
        request: Connection request with optional token

    Returns:
        Connection status
    """
    service = GitHubService(token=request.token)

    connected, rate_limit = await service.test_connection()

    return GitHubConnectionResponse(
        connected=connected,
        rate_limit_remaining=rate_limit,
        message="Connected successfully" if connected else "Connection failed",
    )


@router.post("/issues", response_model=GitHubBatchResponse)
async def get_issues(request: GitHubIssueRequest):
    """Get GitHub issues by numbers.

    Args:
        request: Issue query request

    Returns:
        Issues data
    """
    service = GitHubService()

    issues = []

    for issue_number in request.issue_numbers:
        try:
            issue_data = await service.get_issue(
                request.owner, request.repo, issue_number
            )

            if issue_data:
                issues.append(
                    GitHubIssueResponse(
                        number=issue_data["number"],
                        title=issue_data["title"],
                        state=issue_data["state"],
                        assignee=(
                            issue_data.get("assignee", {}).get("login")
                            if issue_data.get("assignee")
                            else None
                        ),
                        created_at=issue_data["created_at"],
                        updated_at=issue_data["updated_at"],
                        labels=[
                            label["name"] for label in issue_data.get("labels", [])
                        ],
                    )
                )

        except Exception as e:
            logger.error(f"Failed to fetch issue {issue_number}: {e}")
            continue

    return GitHubBatchResponse(issues=issues, count=len(issues))
