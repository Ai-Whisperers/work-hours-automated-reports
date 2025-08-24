# Clockify API Integration

## Overview

The Clockify API integration module handles all communication with Clockify's REST API to fetch time tracking data. This document covers authentication, endpoints, data models, and implementation details.

## API Authentication

### API Key Setup
```python
# Required environment variables
CLOCKIFY_API_KEY = "your-api-key-here"
CLOCKIFY_WORKSPACE_ID = "workspace-id-here"
```

### Headers Configuration
```python
headers = {
    "X-Api-Key": CLOCKIFY_API_KEY,
    "Content-Type": "application/json"
}
```

## Key Endpoints

### 1. Get User Information
```http
GET https://api.clockify.me/api/v1/user
```

### 2. Get Workspaces
```http
GET https://api.clockify.me/api/v1/workspaces
```

### 3. Get Time Entries
```http
GET https://api.clockify.me/api/v1/workspaces/{workspaceId}/user/{userId}/time-entries
```

Parameters:
- `start`: ISO 8601 datetime (required)
- `end`: ISO 8601 datetime (required)
- `page-size`: Number of results per page (max 1000)
- `page`: Page number for pagination

### 4. Get Projects
```http
GET https://api.clockify.me/api/v1/workspaces/{workspaceId}/projects
```

### 5. Get Users in Workspace
```http
GET https://api.clockify.me/api/v1/workspaces/{workspaceId}/users
```

## Data Models

### Time Entry Model
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TimeInterval(BaseModel):
    start: datetime
    end: datetime
    duration: str  # ISO 8601 duration

class TimeEntry(BaseModel):
    id: str
    description: Optional[str] = None
    userId: str
    billable: bool
    projectId: Optional[str] = None
    timeInterval: TimeInterval
    workspaceId: str
    isLocked: bool = False
    customFieldValues: Optional[List[dict]] = None
    tags: Optional[List[str]] = None
    task: Optional[dict] = None
```

### User Model
```python
class User(BaseModel):
    id: str
    email: str
    name: str
    memberships: List[dict]
    profilePicture: Optional[str] = None
    activeWorkspace: str
    defaultWorkspace: str
    settings: dict
```

### Project Model
```python
class Project(BaseModel):
    id: str
    name: str
    hourlyRate: Optional[dict] = None
    clientId: Optional[str] = None
    workspaceId: str
    billable: bool
    memberships: List[dict]
    color: str
    archived: bool
    public: bool
```

## Implementation

### ClockifyClient Class
```python
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseSettings

class ClockifySettings(BaseSettings):
    api_key: str = Field(..., env="CLOCKIFY_API_KEY")
    workspace_id: str = Field(..., env="CLOCKIFY_WORKSPACE_ID")
    base_url: str = "https://api.clockify.me/api/v1"
    
    class Config:
        env_file = ".env"

class ClockifyClient:
    def __init__(self, settings: ClockifySettings):
        self.settings = settings
        self.headers = {
            "X-Api-Key": settings.api_key,
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=self.headers,
            timeout=30.0
        )
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Fetch current user information."""
        response = await self.client.get("/user")
        response.raise_for_status()
        return response.json()
    
    async def get_time_entries(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        page_size: int = 100
    ) -> List[TimeEntry]:
        """
        Fetch time entries for a user within date range.
        Handles pagination automatically.
        """
        all_entries = []
        page = 1
        
        while True:
            params = {
                "start": start_date.isoformat() + "Z",
                "end": end_date.isoformat() + "Z",
                "page-size": page_size,
                "page": page
            }
            
            response = await self.client.get(
                f"/workspaces/{self.settings.workspace_id}/user/{user_id}/time-entries",
                params=params
            )
            response.raise_for_status()
            
            entries = response.json()
            if not entries:
                break
                
            all_entries.extend(entries)
            
            if len(entries) < page_size:
                break
                
            page += 1
            
        return [TimeEntry(**entry) for entry in all_entries]
    
    async def get_all_users(self) -> List[User]:
        """Fetch all users in workspace."""
        response = await self.client.get(
            f"/workspaces/{self.settings.workspace_id}/users"
        )
        response.raise_for_status()
        return [User(**user) for user in response.json()]
    
    async def get_projects(self, archived: bool = False) -> List[Project]:
        """Fetch all projects in workspace."""
        params = {"archived": archived}
        response = await self.client.get(
            f"/workspaces/{self.settings.workspace_id}/projects",
            params=params
        )
        response.raise_for_status()
        return [Project(**project) for project in response.json()]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

## Error Handling

### Common Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| 401 | Unauthorized | Check API key validity |
| 403 | Forbidden | Check workspace permissions |
| 404 | Not Found | Verify resource IDs |
| 429 | Rate Limited | Implement exponential backoff |
| 500 | Server Error | Retry with backoff |

### Retry Strategy
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(self, endpoint: str, **kwargs):
    """Fetch with automatic retry on failure."""
    response = await self.client.get(endpoint, **kwargs)
    response.raise_for_status()
    return response.json()
```

## Rate Limiting

Clockify API has the following rate limits:
- **Standard**: 10 requests per second
- **Bulk operations**: 5 requests per second

### Rate Limiter Implementation
```python
import asyncio
from typing import Any, Callable

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.semaphore = asyncio.Semaphore(calls)
        self.timestamps = []
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        now = asyncio.get_event_loop().time()
        
        # Clean old timestamps
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        
        # Wait if necessary
        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.timestamps.append(now)
    
    async def __aexit__(self, *args):
        self.semaphore.release()

# Usage
rate_limiter = RateLimiter(calls=10, period=1.0)

async with rate_limiter:
    response = await client.get_time_entries(...)
```

## Caching Strategy

### Local Cache Implementation
```python
from functools import lru_cache
from datetime import datetime, timedelta
import pickle
import os

class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint and parameters."""
        import hashlib
        key_str = f"{endpoint}:{sorted(params.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, max_age: timedelta = timedelta(hours=1)):
        """Get cached data if not expired."""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(cache_file)
        )
        if file_age > max_age:
            return None
        
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    
    def set(self, key: str, data: Any):
        """Store data in cache."""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        with open(cache_file, "wb") as f:
            pickle.dump(data, f)
```

## Testing

### Mock Responses
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_clockify_client():
    client = AsyncMock(spec=ClockifyClient)
    client.get_time_entries.return_value = [
        TimeEntry(
            id="1",
            description="Working on #12345",
            userId="user1",
            billable=True,
            timeInterval=TimeInterval(
                start=datetime(2024, 1, 1, 9, 0),
                end=datetime(2024, 1, 1, 17, 0),
                duration="PT8H"
            ),
            workspaceId="workspace1"
        )
    ]
    return client

@pytest.mark.asyncio
async def test_fetch_time_entries(mock_clockify_client):
    entries = await mock_clockify_client.get_time_entries(
        user_id="user1",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    assert len(entries) == 1
    assert entries[0].description == "Working on #12345"
```

## Best Practices

1. **Always use pagination** for large datasets
2. **Implement retry logic** for transient failures
3. **Cache frequently accessed data** (projects, users)
4. **Use async/await** for concurrent API calls
5. **Validate data with Pydantic** models
6. **Log all API interactions** for debugging
7. **Handle timezone conversions** properly
8. **Respect rate limits** to avoid throttling

## Troubleshooting

### Common Issues

1. **Missing time entries**
   - Check date range includes timezone
   - Verify user has logged time
   - Check workspace ID is correct

2. **Authentication failures**
   - Regenerate API key
   - Check key hasn't expired
   - Verify workspace access

3. **Pagination issues**
   - Ensure page size ≤ 1000
   - Handle empty pages correctly
   - Check for off-by-one errors

## References

- [Official Clockify API Documentation](https://docs.clockify.me/)
- [API Playground](https://clockify.me/developers-api)
- [Postman Collection](https://www.postman.com/clockify/workspace/clockify-api)