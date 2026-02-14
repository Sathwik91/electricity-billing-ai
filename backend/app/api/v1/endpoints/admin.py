from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import UsageData

router = APIRouter()

@router.get("/usage-data-status")
async def usage_data_status(db: AsyncSession = Depends(get_db)):
    """Check usage data generation status"""
    
    # Last 24 hours
    last_24h = datetime.now() - timedelta(hours=24)
    result = await db.execute(
        select(
            func.count(UsageData.id).label('total_records'),
            func.min(UsageData.timestamp).label('oldest'),
            func.max(UsageData.timestamp).label('newest')
        ).where(UsageData.timestamp >= last_24h)
    )
    
    stats = result.first()
    
    return {
        "status": "healthy",
        "last_24_hours": {
            "total_records": stats.total_records,
            "oldest_record": stats.oldest.isoformat() if stats.oldest else None,
            "newest_record": stats.newest.isoformat() if stats.newest else None
        },
        "expected_records_per_hour": 5,  # 5 users
        "message": "Usage data is being generated automatically every hour"
    }