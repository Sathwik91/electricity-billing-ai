"""
Export endpoints for generating reports
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UsageData
from app.services.export_service import export_service

router = APIRouter()


@router.get("/bill-report/pdf")
async def export_bill_pdf(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export bill report as PDF"""
    
    # Get user data
    user_data = {
        'full_name': current_user.full_name,
        'email': current_user.email
    }
    
    # Get prediction data (you'll need to import from predictions endpoint logic)
    from app.api.v1.endpoints.predictions import get_current_month_prediction
    prediction_data = await get_current_month_prediction(current_user, db)
    
    # Get usage history
    result = await db.execute(
        select(
            func.date(UsageData.timestamp).label('date'),
            func.sum(UsageData.consumption_kwh).label('consumption_kwh')
        )
        .filter(UsageData.user_id == current_user.id)
        .group_by(func.date(UsageData.timestamp))
        .order_by(func.date(UsageData.timestamp).desc())
        .limit(30)
    )
    
    usage_data = [
        {'date': str(row.date), 'consumption_kwh': float(row.consumption_kwh)}
        for row in result
    ]
    
    # Generate PDF
    pdf_buffer = export_service.generate_bill_pdf(user_data, prediction_data, usage_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=bill_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )


@router.get("/usage/csv")
async def export_usage_csv(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export usage data as CSV"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(UsageData)
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= start_date
        )
        .order_by(UsageData.timestamp.desc())
    )
    
    records = result.scalars().all()
    usage_data = [
        {
            'timestamp': r.timestamp.isoformat(),
            'consumption_kwh': r.consumption_kwh,
            'hour_of_day': r.hour_of_day,
            'is_weekend': r.is_weekend,
            'temperature': r.temperature_celsius,
            'humidity': r.humidity_percentage
        }
        for r in records
    ]
    
    csv_buffer = export_service.generate_usage_csv(usage_data)
    
    return Response(
        content=csv_buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=usage_data_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/usage/excel")
async def export_usage_excel(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export complete report as Excel"""
    
    # Get usage data
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(UsageData.timestamp).label('date'),
            func.sum(UsageData.consumption_kwh).label('consumption_kwh')
        )
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= start_date
        )
        .group_by(func.date(UsageData.timestamp))
        .order_by(func.date(UsageData.timestamp).desc())
    )
    
    usage_data = [
        {'date': str(row.date), 'consumption_kwh': float(row.consumption_kwh)}
        for row in result
    ]
    
    # Get prediction
    from app.api.v1.endpoints.predictions import get_current_month_prediction
    prediction_data = await get_current_month_prediction(current_user, db)
    
    excel_buffer = export_service.generate_usage_excel(usage_data, prediction_data)
    
    return Response(
        content=excel_buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=electricity_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )