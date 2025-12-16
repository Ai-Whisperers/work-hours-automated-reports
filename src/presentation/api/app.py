"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ...infrastructure.config import get_settings
from .routers import reports, health, websockets
from .pipelines import azure_devops, github, clockify


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    app = FastAPI(
        title="Work Hours Automated Reports API",
        description="API for generating time tracking reports from Clockify and Azure DevOps",
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Next.js default port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(websockets.router, prefix="/api", tags=["websockets"])

    # Include pipeline routers
    app.include_router(
        azure_devops.router, prefix="/api/pipelines/azure-devops", tags=["Azure DevOps"]
    )
    app.include_router(github.router, prefix="/api/pipelines/github", tags=["GitHub"])
    app.include_router(
        clockify.router, prefix="/api/pipelines/clockify", tags=["Clockify"]
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.debug else "An error occurred",
            },
        )

    return app


app = create_app()
