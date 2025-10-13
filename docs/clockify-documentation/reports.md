# Reports API

Base path: `/v1/workspaces/{workspaceId}/reports`

## Report Types

### Detailed Report
```
POST /v1/workspaces/{workspaceId}/reports/detailed
```

Returns individual time entries with full details.

### Summary Report
```
POST /v1/workspaces/{workspaceId}/reports/summary
```

Returns aggregated time data by project, user, or other dimensions.

## Request Body Structure

```json
{
  "dateRangeStart": "2024-01-01T00:00:00.000Z",
  "dateRangeEnd": "2024-01-31T23:59:59.999Z",
  "detailedFilter": {
    "page": 1,
    "pageSize": 50,
    "sortColumn": "DATE",
    "sortOrder": "DESCENDING"
  },
  "users": {
    "ids": ["user-id-1", "user-id-2"],
    "contains": "CONTAINS",
    "status": "ALL"
  },
  "projects": {
    "ids": ["project-id-1"],
    "contains": "CONTAINS"
  },
  "tags": {
    "ids": ["tag-id-1"],
    "contains": "CONTAINS"
  },
  "description": "search text",
  "exportType": "JSON"
}
```

## Filter Options

### Date Range
- `dateRangeStart` - Start datetime (ISO 8601)
- `dateRangeEnd` - End datetime (ISO 8601)

### User Filter
- `ids` - Array of user IDs
- `contains` - `CONTAINS` or `DOES_NOT_CONTAIN`
- `status` - `ACTIVE`, `INACTIVE`, or `ALL`

### Project Filter
- `ids` - Array of project IDs
- `contains` - `CONTAINS` or `DOES_NOT_CONTAIN`

### Tag Filter
- `ids` - Array of tag IDs
- `contains` - `CONTAINS` or `DOES_NOT_CONTAIN`

### Sorting
- `sortColumn` - `DATE`, `USER`, `PROJECT`, `DESCRIPTION`, `DURATION`
- `sortOrder` - `ASCENDING` or `DESCENDING`

### Pagination
- `page` - Page number (1-indexed)
- `pageSize` - Results per page (max 200)

## Response Format

### Detailed Report Response
```json
{
  "timeentries": [
    {
      "id": "entry-id",
      "description": "Work description",
      "userId": "user-id",
      "projectId": "project-id",
      "timeInterval": {
        "start": "2024-01-01T09:00:00Z",
        "end": "2024-01-01T17:00:00Z",
        "duration": "PT8H"
      },
      "tags": [{"id": "tag-id", "name": "tag-name"}]
    }
  ],
  "totals": [
    {
      "totalTime": 28800,
      "totalBillableTime": 28800
    }
  ]
}
```

## Common Use Cases

### Get All Time Entries for Period
```json
{
  "dateRangeStart": "2024-01-01T00:00:00.000Z",
  "dateRangeEnd": "2024-01-31T23:59:59.999Z",
  "exportType": "JSON"
}
```

### Get Billable Time by Project
```json
{
  "dateRangeStart": "2024-01-01T00:00:00.000Z",
  "dateRangeEnd": "2024-01-31T23:59:59.999Z",
  "projects": {
    "ids": ["project-id"],
    "contains": "CONTAINS"
  },
  "exportType": "JSON"
}
```
