"""
Usage data endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UsageData

router = APIRouter()


@router.get("/current")
async def get_current_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get latest usage reading"""
    result = await db.execute(
        select(UsageData)
        .filter(UsageData.user_id == current_user.id)
        .order_by(UsageData.timestamp.desc())
        .limit(1)
    )
    usage = result.scalar_one_or_none()
    
    if not usage:
        return {"message": "No usage data found"}
    
    return {
        "timestamp": usage.timestamp,
        "consumption_kwh": usage.consumption_kwh,
        "temperature_celsius": usage.temperature_celsius,
        "humidity_percentage": usage.humidity_percentage,
        "hour_of_day": usage.hour_of_day,
        "is_weekend": usage.is_weekend
    }


@router.get("/history")
async def get_usage_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage history"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily aggregated data
    result = await db.execute(
        select(
            func.date(UsageData.timestamp).label('date'),
            func.sum(UsageData.consumption_kwh).label('total_consumption_kwh'),
            func.avg(UsageData.consumption_kwh).label('avg_consumption_kwh'),
            func.max(UsageData.consumption_kwh).label('peak_consumption_kwh'),
            func.avg(UsageData.temperature_celsius).label('avg_temperature')
        )
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= start_date
        )
        .group_by(func.date(UsageData.timestamp))
        .order_by(func.date(UsageData.timestamp))
    )
    
    data = []
    for row in result:
        data.append({
            "date": str(row.date),
            "total_consumption_kwh": float(row.total_consumption_kwh or 0),
            "avg_consumption_kwh": float(row.avg_consumption_kwh or 0),
            "peak_consumption_kwh": float(row.peak_consumption_kwh or 0),
            "avg_temperature": float(row.avg_temperature or 0) if row.avg_temperature else None
        })
    
    return data


@router.get("/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics"""
    # Last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(
            func.sum(UsageData.consumption_kwh).label('total'),
            func.avg(UsageData.consumption_kwh).label('average'),
            func.max(UsageData.consumption_kwh).label('peak'),
            func.count(UsageData.id).label('count')
        )
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= start_date
        )
    )
    
    stats = result.first()
    
    return {
        "total_consumption_kwh": float(stats.total or 0),
        "average_consumption_kwh": float(stats.average or 0),
        "peak_consumption_kwh": float(stats.peak or 0),
        "data_points": int(stats.count or 0),
        "period_days": 30
    }