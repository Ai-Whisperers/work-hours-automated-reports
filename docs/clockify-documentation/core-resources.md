# Core Resources

## Workspace

Base path: `/v1/workspaces`

### Get All Workspaces
```
GET /v1/workspaces
```

### Get Workspace Details
```
GET /v1/workspaces/{workspaceId}
```

## User

Base path: `/v1/workspaces/{workspaceId}/users`

### Get Current User
```
GET /v1/user
```

### Get Workspace Users
```
GET /v1/workspaces/{workspaceId}/users
```

**Query Parameters**:
- `status` - `ACTIVE`, `INACTIVE`, or `ALL`
- `name` - Filter by name
- `email` - Filter by email
- `page-size` - Results per page

### Get Specific User
```
GET /v1/workspaces/{workspaceId}/users/{userId}
```

## Project

Base path: `/v1/workspaces/{workspaceId}/projects`

### Get All Projects
```
GET /v1/workspaces/{workspaceId}/projects
```

**Query Parameters**:
- `archived` - Include archived (default: false)
- `name` - Filter by name
- `clients` - Client IDs filter
- `page-size` - Results per page

### Get Project Details
```
GET /v1/workspaces/{workspaceId}/projects/{projectId}
```

### Create Project
```
POST /v1/workspaces/{workspaceId}/projects
```

**Body**:
```json
{
  "name": "Project Name",
  "clientId": "client-id",
  "color": "#FF0000",
  "billable": true,
  "isPublic": true
}
```

## Task

Base path: `/v1/workspaces/{workspaceId}/projects/{projectId}/tasks`

### Get Tasks for Project
```
GET /v1/workspaces/{workspaceId}/projects/{projectId}/tasks
```

### Create Task
```
POST /v1/workspaces/{workspaceId}/projects/{projectId}/tasks
```

**Body**:
```json
{
  "name": "Task Name",
  "assigneeIds": ["user-id-1"],
  "status": "ACTIVE"
}
```

## Tag

Base path: `/v1/workspaces/{workspaceId}/tags`

### Get All Tags
```
GET /v1/workspaces/{workspaceId}/tags
```

### Create Tag
```
POST /v1/workspaces/{workspaceId}/tags
```

**Body**:
```json
{
  "name": "Tag Name"
}
```

## Client

Base path: `/v1/workspaces/{workspaceId}/clients`

### Get All Clients
```
GET /v1/workspaces/{workspaceId}/clients
```

**Query Parameters**:
- `archived` - Include archived (default: false)
- `name` - Filter by name
- `page-size` - Results per page

### Create Client
```
POST /v1/workspaces/{workspaceId}/clients
```

**Body**:
```json
{
  "name": "Client Name",
  "email": "client@example.com"
}
```

## Common Response Structures

### Workspace
```json
{
  "id": "workspace-id",
  "name": "Workspace Name",
  "memberships": []
}
```

### User
```json
{
  "id": "user-id",
  "email": "user@example.com",
  "name": "User Name",
  "activeWorkspace": "workspace-id",
  "defaultWorkspace": "workspace-id"
}
```

### Project
```json
{
  "id": "project-id",
  "name": "Project Name",
  "clientId": "client-id",
  "color": "#FF0000",
  "billable": true,
  "archived": false
}
```
