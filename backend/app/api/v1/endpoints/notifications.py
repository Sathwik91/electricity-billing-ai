"""
Notification endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UsageData
from pydantic import BaseModel

router = APIRouter()


class NotificationSettings(BaseModel):
    high_consumption_alerts: bool = True
    daily_summary: bool = True
    bill_predictions: bool = True
    recommendations: bool = True
    threshold_kwh: float = 50.0
    notification_time: str = "20:00"


class PushTokenRequest(BaseModel):
    token: str
    device_type: str = "mobile"


@router.post("/register-token")
async def register_push_token(
    request: PushTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Register device push notification token"""
    # In a real app, store this in database
    # For now, just acknowledge
    return {
        "status": "success",
        "message": "Push token registered",
        "token": request.token[:20] + "..."
    }


@router.get("/settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user)
):
    """Get user notification settings"""
    # In a real app, load from database
    return NotificationSettings()


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_active_user)
):
    """Update notification settings"""
    # In a real app, save to database
    return {
        "status": "success",
        "settings": settings
    }


@router.get("/check-alerts")
async def check_for_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if any alerts should be sent"""
    alerts = []
    
    # Check today's consumption
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.sum(UsageData.consumption_kwh))
        .filter(
            UsageData.user_id == current_user.id,
            func.date(UsageData.timestamp) == today
        )
    )
    today_consumption = float(result.scalar() or 0)
    
    # High consumption alert
    threshold = 50.0  # Should come from user settings
    if today_consumption > threshold:
        alerts.append({
            "type": "high_consumption",
            "severity": "warning",
            "title": "High Consumption Alert",
            "message": f"Today's usage ({today_consumption:.1f} kWh) exceeded threshold",
            "consumption": today_consumption,
            "threshold": threshold
        })
    
    # Check if bill prediction changed significantly
    # (Implement logic here)
    
    return {
        "alerts": alerts,
        "count": len(alerts)
    }