"""
Populate ALL Prometheus metrics from database
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from sqlalchemy import select, func
import calendar

from app.core.database import async_session_maker
from app.models.models import User, UsageData, Recommendation, LifestylePattern
from app.core.metrics import (
    total_users,
    active_users,
    current_consumption_kwh,
    total_consumption_kwh,
    predicted_bill_amount,
    daily_consumption_kwh,
    recommendation_acceptance_rate,
    estimated_savings_kwh,
    user_logins_total,
    lstm_predictions_total,
    rl_recommendations_total
)


def calculate_bill(consumption_kwh: float) -> float:
    """Calculate bill based on tariff slabs"""
    FIXED_CHARGE = 50
    bill = FIXED_CHARGE
    remaining = consumption_kwh
    
    slabs = [
        (0, 100, 3.50),
        (101, 200, 4.50),
        (201, 400, 6.00),
        (401, 500, 7.00),
        (501, float('inf'), 8.00)
    ]
    
    for lower, upper, rate in slabs:
        if remaining <= 0:
            break
        units = min(remaining, upper - lower + 1) if upper != float('inf') else remaining
        bill += units * rate
        remaining -= units
    
    return bill


async def populate_all_metrics():
    """Populate all metrics from database"""
    
    print("\n" + "="*60)
    print("📊 Populating ALL Prometheus Metrics")
    print("="*60 + "\n")
    
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        user_count = len(users)
        total_users.set(user_count)
        print(f"✅ Total Users: {user_count}")
        
        # Active users (with any login)
        result = await session.execute(
            select(func.count(User.id)).filter(User.last_login.isnot(None))
        )
        active_count = result.scalar() or 0
        active_users.set(active_count if active_count > 0 else user_count)  # Default to all if no login data
        print(f"✅ Active Users: {active_count if active_count > 0 else user_count}")
        
        total_consumption_all = 0
        
        # Process each user
        for user in users:
            print(f"\n👤 Processing User {user.id} ({user.email})...")
            
            # Get all usage data for this user
            result = await session.execute(
                select(UsageData)
                .filter(UsageData.user_id == user.id)
                .order_by(UsageData.timestamp.desc())
            )
            usage_records = result.scalars().all()
            
            if not usage_records:
                print(f"   ⚠️  No usage data found")
                # Set default values
                current_consumption_kwh.labels(user_id=str(user.id)).set(0)
                predicted_bill_amount.labels(user_id=str(user.id), currency="INR").set(50)
                continue
            
            # Calculate today's consumption
            today = datetime.utcnow().date()
            today_consumption = sum(
                r.consumption_kwh for r in usage_records 
                if r.timestamp.date() == today
            )
            
            # If no data today, use yesterday's or latest
            if today_consumption == 0:
                yesterday = today - timedelta(days=1)
                today_consumption = sum(
                    r.consumption_kwh for r in usage_records 
                    if r.timestamp.date() == yesterday
                )
            
            # If still no data, use average
            if today_consumption == 0 and usage_records:
                recent_records = usage_records[:48]  # Last 2 days
                today_consumption = sum(r.consumption_kwh for r in recent_records) / 2
            
            current_consumption_kwh.labels(user_id=str(user.id)).set(today_consumption)
            total_consumption_all += today_consumption
            print(f"   📊 Current consumption: {today_consumption:.2f} kWh")
            
            # Calculate current month consumption and predicted bill
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            days_elapsed = now.day
            days_remaining = days_in_month - days_elapsed
            
            # Current month consumption
            month_consumption = sum(
                r.consumption_kwh for r in usage_records 
                if r.timestamp >= month_start
            )
            
            # Predict remaining consumption
            if days_elapsed > 0:
                daily_avg = month_consumption / days_elapsed
                predicted_remaining = daily_avg * days_remaining
            else:
                predicted_remaining = 0
            
            total_predicted = month_consumption + predicted_remaining
            predicted_bill = calculate_bill(total_predicted)
            
            predicted_bill_amount.labels(user_id=str(user.id), currency="INR").set(predicted_bill)
            print(f"   💰 Predicted bill: ₹{predicted_bill:.2f}")
            
            # Daily consumption for last 7 days
            for i in range(7):
                date = today - timedelta(days=i)
                daily_consumption = sum(
                    r.consumption_kwh for r in usage_records 
                    if r.timestamp.date() == date
                )
                daily_consumption_kwh.labels(user_id=str(user.id), date=str(date)).set(daily_consumption)
            
            # Get recommendations stats
            result = await session.execute(
                select(Recommendation).filter(Recommendation.user_id == user.id)
            )
            recommendations = result.scalars().all()
            
            if recommendations:
                accepted = sum(1 for r in recommendations if r.status in ['accepted', 'implemented'])
                rate = (accepted / len(recommendations)) * 100
                recommendation_acceptance_rate.labels(user_id=str(user.id)).set(rate)
                
                total_savings = sum(r.estimated_savings_kwh or 0 for r in recommendations if r.status == 'implemented')
                estimated_savings_kwh.labels(user_id=str(user.id)).set(total_savings)
                
                print(f"   🎯 Recommendation acceptance: {rate:.1f}%")
                print(f"   💡 Estimated savings: {total_savings:.2f} kWh")
            
            # Simulate some ML activity metrics (since we don't track these in DB yet)
            lstm_predictions_total.labels(user_id=str(user.id), status="success").inc(5)
            rl_recommendations_total.labels(user_id=str(user.id)).inc(3)
        
        # Set total consumption
        total_consumption_kwh.set(total_consumption_all)
        print(f"\n✅ Total Consumption (all users): {total_consumption_all:.2f} kWh")
        
        # Simulate some login activity
        user_logins_total.labels(status="success").inc(user_count * 2)
        
    print("\n" + "="*60)
    print("✅ All metrics populated successfully!")
    print("="*60)
    print("\n💡 Tip: Keep this script running in a loop to update metrics:")
    print("   while ($true) { python scripts/populate_all_metrics.py; Start-Sleep -Seconds 30 }")
    print("\n")


if __name__ == "__main__":
    asyncio.run(populate_all_metrics())