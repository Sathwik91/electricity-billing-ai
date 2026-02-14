"""
Lifestyle patterns endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, LifestylePattern

router = APIRouter()


@router.get("/")
async def get_lifestyle_patterns(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learned lifestyle patterns"""
    result = await db.execute(
        select(LifestylePattern)
        .filter(LifestylePattern.user_id == current_user.id)
    )
    patterns = result.scalars().all()
    
    response = {}
    for pattern in patterns:
        response[pattern.pattern_type] = {
            **pattern.pattern_data,
            'confidence': pattern.confidence,
            'last_observed': pattern.last_observed.isoformat() if pattern.last_observed else None
        }
    
    return response


@router.get("/summary")
async def get_pattern_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get human-readable pattern summary"""
    result = await db.execute(
        select(LifestylePattern)
        .filter(LifestylePattern.user_id == current_user.id)
    )
    patterns = result.scalars().all()
    
    summary = []
    
    for pattern in patterns:
        data = pattern.pattern_data
        
        if pattern.pattern_type == 'sleep_cycle' and data.get('detected'):
            summary.append(
                f"Sleep: {data['sleep_start_hour']}:00 - {data['sleep_end_hour']}:00 "
                f"({data['sleep_duration_hours']}h)"
            )
        
        elif pattern.pattern_type == 'work_hours' and data.get('detected'):
            if data.get('works_from_home'):
                summary.append("Works from home")
            else:
                summary.append(
                    f"Work: {data['work_start_hour']}:00 - {data['work_end_hour']}:00"
                )
        
        elif pattern.pattern_type == 'weekend_pattern' and data.get('detected'):
            summary.append(f"Weekend: {data['pattern_type']}")
        
        elif pattern.pattern_type == 'seasonal_pattern' and data.get('detected'):
            if data.get('likely_has_ac'):
                summary.append("Has AC (high summer usage)")
    
    return {
        'summary': ' | '.join(summary) if summary else 'Not enough data to detect patterns',
        'patterns_detected': len(summary)
    }