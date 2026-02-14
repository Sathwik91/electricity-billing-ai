"""
Alerts endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User

router = APIRouter()


@router.get("/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active alerts"""
    
    # Return empty list for now - alerts will be generated based on predictions
    return []