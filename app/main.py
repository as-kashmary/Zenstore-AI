"""
FastAPI application factory.

- Registers all API routers
- Runs SQLAlchemy `create_all` on startup (no Alembic)
- Exposes /health for liveness checks
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.base import init_db

logger = logging.getLogger("zenstore")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    logging.basicConfig(
        level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logger.info("Starting ZenStore AI  (env=%s)", settings.APP_ENV)

    # Create all tables that are registered with Base.metadata
    await init_db()
    logger.info("Database tables verified / created.")

    yield  # ── application is running ──

    logger.info("Shutting down ZenStore AI.")


def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    application = FastAPI(
        title="ZenStore AI",
        description=(
            "RESTful backend that accepts raw product data, enriches it "
            "with LLM-generated marketing descriptions, and processes "
            "bulk uploads asynchronously."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )


    # ── Health endpoint ──────────────────────────────────
    @application.get(
        "/health",
        tags=["Health"],
        summary="Liveness / readiness probe",
    )
    async def health_check():
        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
        }

    return application


app = create_app()