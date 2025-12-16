"""GitHub pipeline service."""

import logging
from typing import Optional
import httpx


logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub operations."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub service.

        Args:
            token: Optional GitHub Personal Access Token
        """
        self.token = token
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> dict:
        """Get headers for GitHub API requests.

        Returns:
            Headers dictionary
        """
        headers = {"Accept": "application/vnd.github.v3+json"}

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        return headers

    async def test_connection(self) -> tuple[bool, Optional[int]]:
        """Test GitHub connection and get rate limit.

        Returns:
            Tuple of (connected, rate_limit_remaining)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/rate_limit", headers=self._get_headers()
                )

                if response.status_code == 200:
                    data = response.json()
                    rate_limit = data.get("rate", {}).get("remaining", 0)
                    return True, rate_limit

                return False, None

        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False, None

    async def get_issue(
        self, owner: str, repo: str, issue_number: int
    ) -> Optional[dict]:
        """Get a GitHub issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Issue data or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    return response.json()

                return None

        except Exception as e:
            logger.error(f"Failed to get GitHub issue: {e}")
            return None
