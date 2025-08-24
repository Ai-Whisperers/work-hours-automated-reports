# Azure DevOps API Integration

## Overview

The Azure DevOps API integration module manages all interactions with Azure DevOps REST API to fetch Work Items, iterations, and project data. This document covers authentication, endpoints, data models, and implementation patterns.

## API Authentication

### Personal Access Token (PAT)
```python
# Required environment variables
ADO_ORG = "your-organization"
ADO_PROJECT = "your-project"
ADO_PAT = "your-personal-access-token"
```

### Authentication Header
```python
import base64

# Encode PAT for Basic Auth
encoded_pat = base64.b64encode(f":{ADO_PAT}".encode()).decode()
headers = {
    "Authorization": f"Basic {encoded_pat}",
    "Content-Type": "application/json"
}
```

## Base URL Structure
```
https://dev.azure.com/{organization}/{project}/_apis/
```

## Key Endpoints

### 1. Get Work Item by ID
```http
GET https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{id}?api-version=7.0
```

### 2. Get Multiple Work Items (Batch)
```http
GET https://dev.azure.com/{organization}/{project}/_apis/wit/workitems?ids={ids}&api-version=7.0
```
Parameters:
- `ids`: Comma-separated list of work item IDs (max 200)
- `fields`: Comma-separated list of field names to return
- `$expand`: Relations, Fields, Links, All, None

### 3. Query Work Items (WIQL)
```http
POST https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=7.0
```
Body:
```json
{
  "query": "SELECT [System.Id], [System.Title], [System.State] FROM workitems WHERE [System.TeamProject] = @project"
}
```

### 4. Get Iterations
```http
GET https://dev.azure.com/{organization}/{project}/{team}/_apis/work/teamsettings/iterations?api-version=7.0
```

### 5. Get Areas
```http
GET https://dev.azure.com/{organization}/{project}/_apis/wit/classificationnodes/areas?api-version=7.0
```

## Data Models

### Work Item Model
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class WorkItemFields(BaseModel):
    system_id: int = Field(alias="System.Id")
    system_title: str = Field(alias="System.Title")
    system_work_item_type: str = Field(alias="System.WorkItemType")
    system_state: str = Field(alias="System.State")
    system_assigned_to: Optional[Dict[str, str]] = Field(None, alias="System.AssignedTo")
    system_created_date: datetime = Field(alias="System.CreatedDate")
    system_changed_date: datetime = Field(alias="System.ChangedDate")
    system_tags: Optional[str] = Field(None, alias="System.Tags")
    system_area_path: str = Field(alias="System.AreaPath")
    system_iteration_path: str = Field(alias="System.IterationPath")
    microsoft_vsts_scheduling_effort: Optional[float] = Field(None, alias="Microsoft.VSTS.Scheduling.Effort")
    microsoft_vsts_scheduling_story_points: Optional[float] = Field(None, alias="Microsoft.VSTS.Scheduling.StoryPoints")
    microsoft_vsts_scheduling_remaining_work: Optional[float] = Field(None, alias="Microsoft.VSTS.Scheduling.RemainingWork")
    microsoft_vsts_scheduling_completed_work: Optional[float] = Field(None, alias="Microsoft.VSTS.Scheduling.CompletedWork")
    
    class Config:
        allow_population_by_field_name = True

class WorkItem(BaseModel):
    id: int
    rev: int
    fields: Dict[str, Any]  # Raw fields
    url: str
    _links: Optional[Dict[str, Any]] = None
    relations: Optional[List[Dict[str, Any]]] = None
    
    def get_field(self, field_name: str, default=None):
        """Safe field accessor."""
        return self.fields.get(field_name, default)
    
    @property
    def title(self) -> str:
        return self.get_field("System.Title", "")
    
    @property
    def state(self) -> str:
        return self.get_field("System.State", "")
    
    @property
    def assigned_to(self) -> Optional[str]:
        assignee = self.get_field("System.AssignedTo")
        if assignee and isinstance(assignee, dict):
            return assignee.get("displayName")
        return None
    
    @property
    def work_item_type(self) -> str:
        return self.get_field("System.WorkItemType", "")
```

### Iteration Model
```python
class Iteration(BaseModel):
    id: str
    name: str
    path: str
    attributes: Dict[str, Any]
    url: str
    
    @property
    def start_date(self) -> Optional[datetime]:
        if self.attributes and "startDate" in self.attributes:
            return datetime.fromisoformat(self.attributes["startDate"])
        return None
    
    @property
    def finish_date(self) -> Optional[datetime]:
        if self.attributes and "finishDate" in self.attributes:
            return datetime.fromisoformat(self.attributes["finishDate"])
        return None
```

## Implementation

### AzureDevOpsClient Class
```python
import httpx
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import asyncio
from pydantic import BaseSettings
import base64

class AzureDevOpsSettings(BaseSettings):
    organization: str = Field(..., env="ADO_ORG")
    project: str = Field(..., env="ADO_PROJECT")
    pat: str = Field(..., env="ADO_PAT")
    api_version: str = "7.0"
    
    class Config:
        env_file = ".env"
    
    @property
    def base_url(self) -> str:
        return f"https://dev.azure.com/{self.organization}"

class AzureDevOpsClient:
    def __init__(self, settings: AzureDevOpsSettings):
        self.settings = settings
        
        # Setup authentication
        encoded_pat = base64.b64encode(f":{settings.pat}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_pat}",
            "Content-Type": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            headers=self.headers,
            timeout=30.0
        )
    
    async def get_work_item(self, work_item_id: int) -> Optional[WorkItem]:
        """Fetch a single work item by ID."""
        try:
            response = await self.client.get(
                f"/{self.settings.project}/_apis/wit/workitems/{work_item_id}",
                params={"api-version": self.settings.api_version}
            )
            response.raise_for_status()
            return WorkItem(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_work_items_batch(
        self,
        work_item_ids: List[int],
        fields: Optional[List[str]] = None,
        expand: str = "None"
    ) -> List[WorkItem]:
        """
        Fetch multiple work items in a single request.
        Maximum 200 IDs per request.
        """
        if not work_item_ids:
            return []
        
        # Azure DevOps API limit
        batch_size = 200
        all_items = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            ids_str = ",".join(map(str, batch_ids))
            
            params = {
                "ids": ids_str,
                "api-version": self.settings.api_version,
                "$expand": expand
            }
            
            if fields:
                params["fields"] = ",".join(fields)
            
            response = await self.client.get(
                f"/{self.settings.project}/_apis/wit/workitems",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            items = [WorkItem(**item) for item in data.get("value", [])]
            all_items.extend(items)
        
        return all_items
    
    async def query_work_items(self, wiql: str) -> List[int]:
        """
        Execute a WIQL query and return work item IDs.
        """
        body = {"query": wiql}
        
        response = await self.client.post(
            f"/{self.settings.project}/_apis/wit/wiql",
            params={"api-version": self.settings.api_version},
            json=body
        )
        response.raise_for_status()
        
        data = response.json()
        return [item["id"] for item in data.get("workItems", [])]
    
    async def get_work_items_by_query(
        self,
        wiql: str,
        fields: Optional[List[str]] = None
    ) -> List[WorkItem]:
        """
        Execute WIQL query and fetch full work items.
        """
        # First, get IDs from query
        work_item_ids = await self.query_work_items(wiql)
        
        # Then fetch full work items
        if work_item_ids:
            return await self.get_work_items_batch(work_item_ids, fields)
        return []
    
    async def get_iterations(self, team: Optional[str] = None) -> List[Iteration]:
        """Fetch team iterations."""
        team_path = f"/{team}" if team else ""
        
        response = await self.client.get(
            f"/{self.settings.project}{team_path}/_apis/work/teamsettings/iterations",
            params={"api-version": self.settings.api_version}
        )
        response.raise_for_status()
        
        data = response.json()
        return [Iteration(**item) for item in data.get("value", [])]
    
    async def get_current_iteration(self, team: Optional[str] = None) -> Optional[Iteration]:
        """Get the current active iteration."""
        iterations = await self.get_iterations(team)
        now = datetime.now()
        
        for iteration in iterations:
            if iteration.start_date and iteration.finish_date:
                if iteration.start_date <= now <= iteration.finish_date:
                    return iteration
        return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

## WIQL Query Examples

### Get All User Stories in Current Sprint
```sql
SELECT [System.Id], [System.Title], [System.AssignedTo]
FROM WorkItems
WHERE [System.TeamProject] = @project
  AND [System.WorkItemType] = 'User Story'
  AND [System.IterationPath] UNDER @currentIteration
  AND [System.State] <> 'Closed'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

### Get Tasks Modified in Last 7 Days
```sql
SELECT [System.Id], [System.Title], [System.ChangedDate]
FROM WorkItems
WHERE [System.TeamProject] = @project
  AND [System.WorkItemType] = 'Task'
  AND [System.ChangedDate] >= @today - 7
ORDER BY [System.ChangedDate] DESC
```

### Get Work Items by ID List
```sql
SELECT [System.Id]
FROM WorkItems
WHERE [System.Id] IN (12345, 12346, 12347)
```

## Error Handling

### Common Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| 401 | Unauthorized | Check PAT validity and permissions |
| 403 | Forbidden | Verify project access |
| 404 | Not Found | Work item doesn't exist |
| 400 | Bad Request | Check WIQL syntax |
| 429 | Too Many Requests | Implement rate limiting |

### Retry Strategy with Backoff
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class RateLimitError(Exception):
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, RateLimitError))
)
async def fetch_with_retry(self, endpoint: str, **kwargs):
    """Fetch with automatic retry on failure."""
    try:
        response = await self.client.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Extract retry-after header if available
            retry_after = e.response.headers.get("Retry-After", "60")
            await asyncio.sleep(int(retry_after))
            raise RateLimitError(f"Rate limited, retry after {retry_after}s")
        raise
```

## Batch Processing

### Efficient Work Item Fetching
```python
async def fetch_work_items_from_ids(
    self,
    work_item_ids: Set[int]
) -> Dict[int, WorkItem]:
    """
    Efficiently fetch work items, minimizing API calls.
    """
    # Remove duplicates and sort
    unique_ids = sorted(set(work_item_ids))
    
    # Fetch in batches
    work_items = await self.get_work_items_batch(
        unique_ids,
        fields=[
            "System.Id",
            "System.Title",
            "System.State",
            "System.AssignedTo",
            "System.WorkItemType",
            "System.IterationPath",
            "System.Tags"
        ]
    )
    
    # Create lookup dictionary
    return {wi.id: wi for wi in work_items}
```

## Caching Strategy

### Work Item Cache
```python
from functools import lru_cache
from datetime import datetime, timedelta
import json
import hashlib

class WorkItemCache:
    def __init__(self, ttl: timedelta = timedelta(minutes=15)):
        self.cache = {}
        self.ttl = ttl
    
    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.now() - timestamp > self.ttl
    
    def get(self, work_item_id: int) -> Optional[WorkItem]:
        if work_item_id in self.cache:
            item, timestamp = self.cache[work_item_id]
            if not self._is_expired(timestamp):
                return item
            del self.cache[work_item_id]
        return None
    
    def set(self, work_item: WorkItem):
        self.cache[work_item.id] = (work_item, datetime.now())
    
    def set_many(self, work_items: List[WorkItem]):
        timestamp = datetime.now()
        for item in work_items:
            self.cache[item.id] = (item, timestamp)
    
    def clear_expired(self):
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if self._is_expired(timestamp)
        ]
        for key in expired_keys:
            del self.cache[key]
```

## Performance Optimization

### Concurrent Fetching
```python
async def fetch_work_items_concurrent(
    self,
    work_item_ids: List[int],
    max_concurrent: int = 5
) -> List[WorkItem]:
    """
    Fetch work items with controlled concurrency.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(wi_id: int):
        async with semaphore:
            return await self.get_work_item(wi_id)
    
    tasks = [fetch_with_semaphore(wi_id) for wi_id in work_item_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out errors and None values
    return [r for r in results if isinstance(r, WorkItem)]
```

## Testing

### Mock ADO Client
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_ado_client():
    client = AsyncMock(spec=AzureDevOpsClient)
    
    # Mock work item response
    mock_work_item = WorkItem(
        id=12345,
        rev=1,
        fields={
            "System.Id": 12345,
            "System.Title": "Implement feature X",
            "System.State": "Active",
            "System.WorkItemType": "User Story",
            "System.AssignedTo": {
                "displayName": "John Doe",
                "uniqueName": "john.doe@example.com"
            }
        },
        url="https://dev.azure.com/org/project/_apis/wit/workitems/12345"
    )
    
    client.get_work_item.return_value = mock_work_item
    client.get_work_items_batch.return_value = [mock_work_item]
    
    return client

@pytest.mark.asyncio
async def test_get_work_item(mock_ado_client):
    work_item = await mock_ado_client.get_work_item(12345)
    assert work_item.id == 12345
    assert work_item.title == "Implement feature X"
    assert work_item.assigned_to == "John Doe"
```

## Security Best Practices

1. **PAT Storage**
   - Never commit PATs to source control
   - Use environment variables or secure vaults
   - Rotate PATs regularly

2. **Minimal Permissions**
   - Grant only required scopes (Work Items: Read)
   - Use service accounts for automation

3. **Data Sanitization**
   - Validate all input parameters
   - Escape special characters in WIQL
   - Limit query result sizes

4. **Audit Logging**
   - Log all API access
   - Track data modifications
   - Monitor for suspicious patterns

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify PAT hasn't expired
   - Check organization and project names
   - Ensure PAT has correct scopes

2. **Missing Work Items**
   - Check area/iteration paths
   - Verify query syntax
   - Confirm permissions on work items

3. **Performance Issues**
   - Use batch APIs instead of individual calls
   - Implement caching for frequently accessed items
   - Optimize WIQL queries

4. **Data Inconsistencies**
   - Handle work item state transitions
   - Account for deleted/moved items
   - Sync cache with source regularly

## References

- [Azure DevOps REST API Documentation](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
- [WIQL Syntax Reference](https://docs.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
- [API Versioning](https://docs.microsoft.com/en-us/azure/devops/integrate/concepts/rest-api-versioning)
- [Authentication Guide](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate)