"""Health check API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config.settings import Settings, get_settings
from app.database.connection import get_db_session

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Application health check",
    description="Check if the application and its dependencies are healthy"
)
async def health_check(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> dict[str, str]:
    """Main application health check endpoint."""
    try:
        # Test database connection
        await db_session.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": __version__,
    } 