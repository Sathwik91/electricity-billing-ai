"""
Populate initial 30 days of usage data
Run this once to backfill historical data
"""
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.models import User, UsageData


async def populate_initial_data():
    """Generate 30 days of historical usage data"""
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"📊 Populating data for {len(users)} users")
        print("="*60)
        
        for user in users:
            print(f"\n👤 Processing: {user.email}")
            
            # Generate data for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            records_created = 0
            total_consumption = 0
            current_date = start_date
            
            while current_date <= end_date:
                # Generate 24 hourly records for each day
                for hour in range(24):
                    timestamp = current_date.replace(
                        hour=hour, 
                        minute=0, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # Skip future hours
                    if timestamp > datetime.now():
                        break
                    
                    # Check if already exists
                    existing = await session.execute(
                        select(UsageData).where(
                            UsageData.user_id == user.id,
                            UsageData.timestamp == timestamp
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue  # Skip existing records
                    
                    # Base consumption
                    base_consumption = random.uniform(0.5, 2.0)
                    
                    # Time-of-day multipliers
                    if 0 <= hour < 6:  # Night
                        multiplier = random.uniform(0.3, 0.5)
                    elif 6 <= hour < 9:  # Morning
                        multiplier = random.uniform(1.0, 1.5)
                    elif 9 <= hour < 17:  # Day
                        multiplier = random.uniform(0.6, 1.0)
                    elif 17 <= hour < 22:  # Evening
                        multiplier = random.uniform(1.2, 1.8)
                    else:  # Late night
                        multiplier = random.uniform(0.4, 0.6)
                    
                    # Weekend adjustment
                    is_weekend = timestamp.weekday() >= 5
                    if is_weekend:
                        multiplier *= 1.2
                    
                    consumption = base_consumption * multiplier
                    total_consumption += consumption
                    
                    usage_record = UsageData(
                        user_id=user.id,
                        timestamp=timestamp,
                        consumption_kwh=consumption,
                        hour_of_day=hour,
                        is_weekend=is_weekend,
                        temperature_celsius=random.uniform(20, 35),
                        humidity_percentage=random.uniform(40, 80)
                    )
                    
                    session.add(usage_record)
                    records_created += 1
                    
                    # Commit in batches of 100
                    if records_created % 100 == 0:
                        await session.commit()
                        print(f"  ⏳ {records_created} records created...")
                
                current_date += timedelta(days=1)
            
            await session.commit()
            
            print(f"  ✅ Created {records_created} records")
            print(f"  📊 Total consumption: {total_consumption:.1f} kWh")
            print(f"  📈 Average per hour: {total_consumption/records_created:.2f} kWh")
        
        print("\n" + "="*60)
        print("✅ Initial data population complete!")


if __name__ == "__main__":
    print("🚀 Starting initial data population...")
    print("⏰ This may take a few minutes...")
    print()
    asyncio.run(populate_initial_data())