"""Base API client with common functionality."""

import asyncio
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
)

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(APIError):
    """Exception for rate limit errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Exception for authentication errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class NotFoundError(APIError):
    """Exception for not found errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class BaseAPIClient(ABC):
    """Base API client with common functionality.

    Provides retry logic, rate limiting, error handling, and
    connection pooling for API clients.
    """

    def __init__(
        self,
        base_url: str,
        headers: Dict[str, str],
        timeout: int = 30,
        max_retries: int = 3,
        max_connections: int = 10,
    ):
        """Initialize the base API client.

        Args:
            base_url: Base URL for the API
            headers: Default headers for requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            max_connections: Maximum number of concurrent connections
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.timeout = timeout
        self.max_retries = max_retries

        # Configure connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=max_connections, max_connections=max_connections
        )

        # Create async client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(timeout),
            limits=limits,
        )

        # Rate limiting
        self._rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, RateLimitError)
        ),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers

        Returns:
            HTTP response

        Raises:
            APIError: For API errors
            RateLimitError: For rate limit errors
        """
        # Rate limiting
        async with self._rate_limiter:
            # Ensure minimum interval between requests
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - time_since_last)

            # Prepare request
            url = (
                endpoint
                if endpoint.startswith("http")
                else f"{self.base_url}/{endpoint.lstrip('/')}"
            )
            request_headers = {**self.headers, **(headers or {})}

            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                )

                self._last_request_time = asyncio.get_event_loop().time()

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds",
                        retry_after=int(retry_after),
                    )

                # Handle authentication errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Authentication failed. Check your API credentials."
                    )

                # Handle not found errors
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}")

                # Raise for other HTTP errors
                response.raise_for_status()

                return response

            except httpx.TimeoutException as e:
                logger.error(f"Request timeout for {url}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                raise APIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                raise APIError(f"Unexpected error: {e}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response
        """
        response = await self._make_request(
            "GET", endpoint, params=params, headers=headers
        )
        return response.json()

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint
            json_data: JSON body data
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response
        """
        response = await self._make_request(
            "POST", endpoint, params=params, json_data=json_data, headers=headers
        )
        return response.json()

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint: API endpoint
            json_data: JSON body data
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response
        """
        response = await self._make_request(
            "PUT", endpoint, params=params, json_data=json_data, headers=headers
        )
        return response.json()

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers

        Returns:
            True if successful
        """
        response = await self._make_request(
            "DELETE", endpoint, params=params, headers=headers
        )
        return response.status_code in [200, 204]

    async def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get paginated results.

        Args:
            endpoint: API endpoint
            params: Initial query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all items from all pages
        """
        all_items = []
        page = 1
        params = params or {}

        while True:
            # Add pagination parameters
            page_params = {**params, "page": page, "page-size": page_size}

            # Fetch page
            response = await self.get(endpoint, params=page_params)

            # Extract items (implementation specific)
            items = self._extract_items_from_response(response)

            if not items:
                break

            all_items.extend(items)

            # Check if we've reached the maximum pages
            if max_pages and page >= max_pages:
                break

            # Check if there are more pages
            if len(items) < page_size:
                break

            page += 1

        return all_items

    @abstractmethod
    def _extract_items_from_response(
        self, response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract items from paginated response.

        This method should be implemented by subclasses to handle
        API-specific response formats.

        Args:
            response: API response

        Returns:
            List of items from the response
        """
        pass

    async def batch_request(
        self, method: str, endpoints: List[str], batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Make batch requests with concurrency control.

        Args:
            method: HTTP method
            endpoints: List of endpoints to request
            batch_size: Number of concurrent requests

        Returns:
            List of responses
        """
        results = []

        for i in range(0, len(endpoints), batch_size):
            batch = endpoints[i : i + batch_size]
            tasks = [self._make_request(method, endpoint) for endpoint in batch]

            batch_responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in batch_responses:
                if isinstance(response, Exception):
                    logger.error(f"Batch request failed: {response}")
                    results.append(None)
                else:
                    results.append(response.json())

        return results
