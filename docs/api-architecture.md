# API Architecture Documentation

## Overview

The FastAPI backend follows **Clean Architecture** principles with a modular pipeline-based structure. Each integration (Azure DevOps, GitHub, Clockify) is isolated in its own pipeline module with consistent patterns.

## Directory Structure

```
src/presentation/api/
├── __init__.py
├── app.py                          # Main FastAPI application factory
├── middleware/
│   ├── __init__.py
│   └── websocket_manager.py        # WebSocket connection manager
├── schemas/
│   ├── __init__.py
│   ├── common.py                   # Shared Pydantic models
│   └── reports.py                  # Report-specific models
├── routers/
│   ├── __init__.py
│   ├── health.py                   # Health check endpoints
│   ├── reports.py                  # Report generation endpoints
│   └── websockets.py               # WebSocket endpoints
└── pipelines/
    ├── __init__.py
    ├── azure_devops/               # Azure DevOps pipeline
    │   ├── __init__.py
    │   ├── schemas.py              # ADO-specific models
    │   ├── service.py              # Business logic
    │   └── router.py               # FastAPI routes
    ├── github/                     # GitHub pipeline
    │   ├── __init__.py
    │   ├── schemas.py
    │   ├── service.py
    │   └── router.py
    └── clockify/                   # Clockify pipeline
        ├── __init__.py
        ├── schemas.py
        ├── service.py
        └── router.py
```

## Architecture Principles

### 1. Modular Pipelines

Each external integration is organized as a self-contained pipeline with:

- **Schemas** (`schemas.py`): Pydantic models for request/response validation
- **Service** (`service.py`): Business logic and external API interactions
- **Router** (`router.py`): FastAPI endpoint definitions

### 2. Separation of Concerns

- **Routers**: Handle HTTP requests, validation, and responses
- **Services**: Contain business logic and coordinate infrastructure layer
- **Middleware**: Cross-cutting concerns (WebSockets, CORS, etc.)
- **Schemas**: Data validation and serialization

### 3. Dependency Injection

Services use FastAPI's dependency injection:

```python
def get_ado_service() -> AzureDevOpsService:
    return AzureDevOpsService()

@router.get("/connection")
async def check_connection(service: AzureDevOpsService = Depends(get_ado_service)):
    # Service is automatically injected
    pass
```

## API Endpoints

### Core Endpoints

#### Health Checks
- `GET /api/health` - Basic health status
- `GET /api/health/services` - External service connectivity

#### Reports
- `POST /api/reports/generate` - Generate new report
- `GET /api/reports/status/{id}` - Check report status
- `GET /api/reports/download/{id}` - Download completed report

#### WebSockets
- `WS /api/ws` - General WebSocket connection
- `WS /api/ws/report/{id}` - Report-specific updates

### Pipeline Endpoints

#### Azure DevOps (`/api/pipelines/azure-devops`)
- `GET /connection` - Test ADO connection
- `POST /work-items` - Query work items by IDs

#### GitHub (`/api/pipelines/github`)
- `POST /connection` - Test GitHub connection
- `POST /issues` - Query GitHub issues

#### Clockify (`/api/pipelines/clockify`)
- `POST /connection` - Test Clockify connection
- `POST /time-entries` - Query time entries

## WebSocket Architecture

### WebSocket Manager

The `WebSocketManager` class (`middleware/websocket_manager.py`) handles:

- Connection lifecycle management
- Message broadcasting
- Report-specific subscriptions
- Automatic reconnection handling

### Message Types

```typescript
interface WebSocketMessage {
  type: 'progress' | 'status' | 'completed'
  report_id: string
  progress?: number        // 0.0 to 1.0
  message?: string
  status?: string          // 'pending' | 'processing' | 'completed' | 'failed'
  download_url?: string
  error?: string
}
```

### Real-time Updates

Report generation broadcasts updates via WebSocket:

1. **Initialization** (10% progress)
2. **Connecting to services** (20% progress)
3. **Generating report** (50% progress)
4. **Completed** (100% progress) or **Failed** (error message)

## Pipeline Implementation Pattern

Each pipeline follows this structure:

### 1. Schemas (`schemas.py`)

```python
from pydantic import BaseModel, Field

class RequestModel(BaseModel):
    """Request validation."""
    field: str = Field(..., description="Field description")

class ResponseModel(BaseModel):
    """Response serialization."""
    result: str
```

### 2. Service (`service.py`)

```python
class PipelineService:
    """Business logic for pipeline."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None

    async def initialize(self):
        """Lazy initialization of clients."""
        pass

    async def close(self):
        """Clean up resources."""
        pass
```

### 3. Router (`router.py`)

```python
router = APIRouter()

@router.post("/endpoint", response_model=ResponseModel)
async def endpoint(
    request: RequestModel,
    service: PipelineService = Depends(get_service)
):
    """Endpoint documentation."""
    try:
        result = await service.operation(request)
        return result
    finally:
        await service.close()
```

## Error Handling

### Global Exception Handler

All unhandled exceptions are caught by the global handler in `app.py`:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )
```

### Custom Exceptions

Pipeline-specific errors use FastAPI's `HTTPException`:

```python
from fastapi import HTTPException

if not valid:
    raise HTTPException(status_code=400, detail="Invalid request")
```

## CORS Configuration

Cross-Origin Resource Sharing is configured for local development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing

### Running the API

```bash
# Development
python api_server.py

# Production with Uvicorn
uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000

# With workers (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.presentation.api.app:app
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### Testing Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Service status
curl http://localhost:8000/api/health/services

# Generate report
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"format": "excel", "include_unmatched": true}'

# Query work items
curl -X POST http://localhost:8000/api/pipelines/azure-devops/work-items \
  -H "Content-Type: application/json" \
  -d '{"work_item_ids": [12345, 67890]}'
```

## Security Considerations

### Current Implementation

- CORS restricted to localhost (development)
- No authentication (suitable for internal tools)
- Environment variables for sensitive data

### Production Recommendations

1. **Add Authentication**:
   - JWT tokens (`python-jose` already in requirements)
   - API keys for service-to-service
   - OAuth2 for user authentication

2. **Update CORS**:
   - Restrict to specific domains
   - Remove wildcards in production

3. **Rate Limiting**:
   - Add `slowapi` for rate limiting
   - Protect expensive endpoints

4. **Secrets Management**:
   - Use Azure Key Vault or AWS Secrets Manager
   - Never commit `.env` files

## Performance Optimization

### Async Operations

All I/O operations use `async/await`:

```python
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Connection Pooling

HTTP clients reuse connections:

```python
self.client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=5)
)
```

### Background Tasks

Long-running operations use FastAPI background tasks:

```python
@router.post("/generate")
async def generate_report(background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_report_task, report_id)
    return {"status": "queued"}
```

## Monitoring

### Logging

Structured logging throughout:

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing report {report_id}")
logger.error(f"Failed to connect: {error}")
```

### Metrics (Optional)

`prometheus-client` is included for metrics:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
```

## Future Enhancements

1. **Redis Integration**:
   - Replace in-memory report status store
   - Shared state across multiple workers
   - Better WebSocket message queuing

2. **Database Integration**:
   - Persist report history
   - User preferences
   - Audit logging

3. **Task Queue**:
   - Celery for distributed task processing
   - Better scalability for report generation

4. **API Versioning**:
   - `/api/v1/` and `/api/v2/` routes
   - Backward compatibility

5. **GraphQL Support**:
   - Add Strawberry GraphQL
   - Flexible queries for complex reporting

## Troubleshooting

### Common Issues

**WebSocket connection fails**:
- Check CORS settings
- Ensure ws:// protocol (not wss:// in development)
- Verify port 8000 is accessible

**Pipeline endpoints return 500**:
- Check environment variables are set
- Verify API credentials are valid
- Review logs for detailed errors

**Reports not generating**:
- Check Clockify and ADO connectivity
- Verify date range is valid
- Ensure report output directory exists

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [WebSocket Protocol](https://websockets.readthedocs.io/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
