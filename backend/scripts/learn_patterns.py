"""
Learn lifestyle patterns from user data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from sqlalchemy import select
from datetime import datetime

from app.core.database import async_session_maker
from app.models.models import UsageData, User, LifestylePattern
from ml_models.pattern_learning.lifestyle_patterns import LifestylePatternLearner
import numpy as np

def to_json_safe(obj):
    """
    Recursively convert numpy / pandas types to native Python types
    so they can be stored in JSON columns safely.
    """
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    else:
        return obj



async def learn_patterns_for_user(user_id: int):
    """Learn lifestyle patterns for a user"""
    print(f"\n{'='*60}")
    print(f"Learning Patterns for User {user_id}")
    print(f"{'='*60}\n")
    
    async with async_session_maker() as session:
        # Load usage data
        result = await session.execute(
            select(UsageData)
            .filter(UsageData.user_id == user_id)
            .order_by(UsageData.timestamp)
        )
        usage_records = result.scalars().all()
        
        if not usage_records:
            print(f"No data found for user {user_id}")
            return
        
        # Convert to DataFrame
        data = pd.DataFrame([{
            'timestamp': r.timestamp,
            'consumption_kwh': r.consumption_kwh
        } for r in usage_records])
        
        print(f"📊 Analyzing {len(data)} records")
        
        # Initialize pattern learner
        learner = LifestylePatternLearner()
        
        # Learn all patterns
        patterns = learner.learn_all_patterns(data)
        
        # Display results
        print("\n🔍 Detected Patterns:\n")
        
        # Sleep Cycle
        if patterns['sleep_cycle']['detected']:
            sleep = patterns['sleep_cycle']
            print(f"😴 Sleep Cycle:")
            print(f"   • Sleep Time: {sleep['sleep_start_hour']}:00 - {sleep['sleep_end_hour']}:00")
            print(f"   • Duration: {sleep['sleep_duration_hours']} hours")
            print(f"   • Confidence: {sleep['confidence']*100:.0f}%")
        
        # Work Hours
        if patterns['work_hours']['detected']:
            work = patterns['work_hours']
            print(f"\n💼 Work Pattern:")
            if work['works_from_home']:
                print(f"   • Works from home")
            else:
                print(f"   • Works outside: {work['work_start_hour']}:00 - {work['work_end_hour']}:00")
            print(f"   • Confidence: {work['confidence']*100:.0f}%")
        
        # Weekend Pattern
        if patterns['weekend_pattern']['detected']:
            weekend = patterns['weekend_pattern']
            print(f"\n📅 Weekend Pattern:")
            print(f"   • Weekend avg: {weekend['weekend_avg_consumption']:.2f} kWh")
            print(f"   • Weekday avg: {weekend['weekday_avg_consumption']:.2f} kWh")
            print(f"   • Difference: {weekend['difference_percentage']:.1f}%")
            print(f"   • Type: {weekend['pattern_type']}")
        
        # Seasonal Pattern
        if patterns['seasonal_pattern']['detected']:
            seasonal = patterns['seasonal_pattern']
            print(f"\n🌡️ Seasonal Pattern:")
            print(f"   • Seasonality: {seasonal['seasonality_level']}")
            print(f"   • Peak month: {seasonal['peak_month']}")
            print(f"   • Low month: {seasonal['low_month']}")
            if seasonal['likely_has_ac']:
                print(f"   • ⚠️ Likely has AC (high summer usage)")
        
        # Save patterns to database
        await save_patterns_to_db(session, user_id, patterns)
        
        print(f"\n💾 Patterns saved to database")
        
        # Save model
        model_dir = f"models/patterns/user_{user_id}"
        os.makedirs(model_dir, exist_ok=True)
        learner.save(model_dir)
        print(f"💾 Model saved to {model_dir}")


async def save_patterns_to_db(session, user_id: int, patterns: dict):
    from sqlalchemy import delete
    from app.models.models import LifestylePattern

    # Remove old patterns
    await session.execute(
        delete(LifestylePattern).where(LifestylePattern.user_id == user_id)
    )

    now = datetime.utcnow()

    for pattern_type, pattern_data in patterns.items():
        if pattern_type in ["learning_date", "data_points"]:
            continue

        if not pattern_data.get("detected", False):
            continue

        
        safe_pattern_data = to_json_safe(pattern_data)

        pattern = LifestylePattern(
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_data=safe_pattern_data,
            confidence=float(safe_pattern_data.get("confidence", 0.8)),
            occurrences=1,
            last_observed=now,
        )

        session.add(pattern)

    await session.commit()



async def main():
    """Main pattern learning function"""
    print("\n" + "="*60)
    print("🧠 Lifestyle Pattern Learning")
    print("="*60 + "\n")
    
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    print(f"Found {len(users)} users\n")
    
    for user in users:
        try:
            await learn_patterns_for_user(user.id)
        except Exception as e:
            print(f"❌ Error learning patterns for user {user.id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ Pattern learning complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())