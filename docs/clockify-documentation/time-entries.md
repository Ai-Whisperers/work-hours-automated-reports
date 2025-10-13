# Time Entry API

Base path: `/v1/workspaces/{workspaceId}/time-entries`

## Endpoints

### Get Time Entries for User
```
GET /v1/workspaces/{workspaceId}/user/{userId}/time-entries
```

**Query Parameters**:
- `start` - Start date (ISO 8601)
- `end` - End date (ISO 8601)
- `project` - Project ID filter
- `task` - Task ID filter
- `tags` - Tag IDs filter
- `page-size` - Results per page (default 50)

### Get Specific Time Entry
```
GET /v1/workspaces/{workspaceId}/time-entries/{id}
```

### Add Time Entry
```
POST /v1/workspaces/{workspaceId}/time-entries
```

**Body**:
```json
{
  "start": "2024-01-01T09:00:00Z",
  "end": "2024-01-01T17:00:00Z",
  "projectId": "project-id",
  "description": "Work description",
  "tagIds": ["tag-id-1"],
  "taskId": "task-id"
}
```

### Update Time Entry
```
PUT /v1/workspaces/{workspaceId}/time-entries/{id}
```

### Delete Time Entry
```
DELETE /v1/workspaces/{workspaceId}/time-entries/{id}
```

### Stop Running Timer
```
PATCH /v1/workspaces/{workspaceId}/user/{userId}/time-entries
```

### Bulk Edit Time Entries
```
PUT /v1/workspaces/{workspaceId}/time-entries/bulk
```

## Common Operations

### Get Current User Time Entries
```
GET /v1/workspaces/{workspaceId}/user/{userId}/time-entries?start=2024-01-01T00:00:00Z&end=2024-01-31T23:59:59Z
```

### Mark as Invoiced
```
PATCH /v1/workspaces/{workspaceId}/time-entries/invoiced
```

### Duplicate Entry
```
POST /v1/workspaces/{workspaceId}/time-entries/duplicate
```

## Response Format

```json
{
  "id": "entry-id",
  "description": "Work description",
  "userId": "user-id",
  "workspaceId": "workspace-id",
  "projectId": "project-id",
  "taskId": "task-id",
  "timeInterval": {
    "start": "2024-01-01T09:00:00Z",
    "end": "2024-01-01T17:00:00Z",
    "duration": "PT8H"
  },
  "tagIds": ["tag-id-1"]
}
```
