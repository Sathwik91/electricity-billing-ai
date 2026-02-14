"""
Train Reinforcement Learning recommendation engine
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from sqlalchemy import select
from datetime import datetime, timedelta

from app.core.database import async_session_maker
from app.models.models import User, UsageData, LifestylePattern, Recommendation
from rl_recommendation_engine import RLRecommendationEngine, RecommendationAction


async def get_user_state_data(user_id: int):
    """Get user data for state representation"""
    async with async_session_maker() as session:
        # Get user
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Get recent usage
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = await session.execute(
            select(UsageData)
            .filter(
                UsageData.user_id == user_id,
                UsageData.timestamp >= thirty_days_ago
            )
            .order_by(UsageData.timestamp.desc())
        )
        usage_records = result.scalars().all()
        
        if not usage_records:
            return None
        
        # Calculate metrics
        total_consumption = sum(r.consumption_kwh for r in usage_records)
        days = len(set(r.timestamp.date() for r in usage_records))
        avg_daily = total_consumption / max(days, 1)
        
        # Get patterns
        result = await session.execute(
            select(LifestylePattern).filter(LifestylePattern.user_id == user_id)
        )
        patterns = result.scalars().all()
        
        pattern_data = {}
        for p in patterns:
            if p.pattern_type == 'sleep_cycle':
                pattern_data['sleep_regularity'] = p.confidence
            elif p.pattern_type == 'work_hours':
                pattern_data['works_from_home'] = p.pattern_data.get('works_from_home', False)
            elif p.pattern_type == 'weekend_pattern':
                diff = p.pattern_data.get('difference_percentage', 0)
                pattern_data['weekend_spike'] = abs(diff) / 100.0
            elif p.pattern_type == 'seasonal_pattern':
                pattern_data['seasonality'] = 0.3 if p.pattern_data.get('seasonality_level') == 'low' else 0.7
        
        return {
            'user_data': {
                'avg_daily_consumption': avg_daily,
                'consumption_trend': 0.0,  # Calculate from data
                'has_ac': True,  # Assume for now
                'house_size': 150,  # Default
                'occupants': 3,  # Default
                'bill_ratio': 1.0,
                'days_into_month': datetime.utcnow().day,
                'acceptance_rate': 0.5
            },
            'usage_data': {
                'hour': datetime.utcnow().hour,
                'is_weekend': datetime.utcnow().weekday() >= 5,
                'temperature': usage_records[0].temperature_celsius or 25.0
            },
            'patterns': pattern_data
        }


async def simulate_user_feedback(recommendation, user_profile):
    """Simulate user feedback for training"""
    # Simulate different user responses
    
    effort = recommendation['effort_level']
    savings = recommendation['estimated_savings_kwh']
    
    # Acceptance probability
    if effort == 'easy':
        accept_prob = 0.7
    elif effort == 'moderate':
        accept_prob = 0.5
    else:  # hard
        accept_prob = 0.3
    
    # Higher savings increase acceptance
    accept_prob += min(savings / 10.0, 0.2)
    
    accepted = np.random.rand() < accept_prob
    
    if not accepted:
        return {
            'accepted': False,
            'implemented': False,
            'rating': np.random.randint(1, 4),
            'actual_savings': 0,
            'estimated_savings': savings
        }
    
    # Implementation probability (if accepted)
    impl_prob = 0.6 if effort == 'easy' else 0.4 if effort == 'moderate' else 0.2
    implemented = np.random.rand() < impl_prob
    
    if not implemented:
        return {
            'accepted': True,
            'implemented': False,
            'rating': np.random.randint(2, 5),
            'actual_savings': 0,
            'estimated_savings': savings
        }
    
    # Actual savings (with some variance)
    actual_savings = savings * np.random.uniform(0.7, 1.3)
    
    # Rating based on results
    if actual_savings >= savings:
        rating = np.random.randint(4, 6)
    else:
        rating = np.random.randint(3, 5)
    
    return {
        'accepted': True,
        'implemented': True,
        'rating': rating,
        'actual_savings': actual_savings,
        'estimated_savings': savings,
        'time_to_implement': np.random.randint(3, 20)
    }


async def train_rl_for_user(user_id: int, episodes=100):
    """Train RL engine for a user"""
    print(f"\n{'='*60}")
    print(f"Training RL Engine for User {user_id}")
    print(f"{'='*60}\n")
    
    # Get user data
    data = await get_user_state_data(user_id)
    if not data:
        print("❌ No data available")
        return
    
    # Initialize RL engine
    engine = RLRecommendationEngine()
    
    # Training loop
    print(f"🚀 Starting training for {episodes} episodes...\n")
    
    total_reward = 0
    acceptance_rate = 0
    
    for episode in range(episodes):
        # Get current state
        state = engine.get_state(
            data['user_data'],
            data['usage_data'],
            data['patterns']
        )
        
        # Get recommendations
        recommendations = engine.get_recommendations(state, top_k=3)
        
        # Simulate feedback for each recommendation
        episode_reward = 0
        for rec in recommendations:
            feedback = await simulate_user_feedback(rec, data['user_data'])
            
            # Calculate reward
            reward = engine.calculate_reward(feedback)
            episode_reward += reward
            
            # Store experience
            # Next state would be similar (simplified)
            next_state = state.copy()
            next_state[14] = (next_state[14] + (1.0 if feedback['accepted'] else 0.0)) / 2.0
            
            done = False
            engine.remember(state, rec['action_index'], reward, next_state, done)
            
            if feedback['accepted']:
                acceptance_rate += 1
        
        # Train on experience
        if len(engine.memory) >= engine.batch_size:
            engine.replay()
        
        # Update target network periodically
        if episode % 10 == 0:
            engine.update_target_model()
        
        total_reward += episode_reward
        
        # Progress update
        if (episode + 1) % 20 == 0:
            avg_reward = total_reward / (episode + 1)
            acc_rate = acceptance_rate / ((episode + 1) * 3) * 100
            print(f"Episode {episode + 1}/{episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Acceptance: {acc_rate:.1f}% | "
                  f"Epsilon: {engine.epsilon:.3f}")
    
    print(f"\n✅ Training complete!")
    print(f"📈 Total Reward: {total_reward:.2f}")
    print(f"📈 Avg Reward per Episode: {total_reward/episodes:.2f}")
    print(f"📈 Final Acceptance Rate: {acceptance_rate/(episodes*3)*100:.1f}%")
    print(f"📈 Final Epsilon: {engine.epsilon:.3f}")
    
    # Save model
    model_dir = f"models/recommendation/user_{user_id}"
    engine.save(model_dir)
    
    return engine


async def main():
    """Main training function"""
    print("\n" + "="*60)
    print("🤖 Reinforcement Learning Training")
    print("="*60 + "\n")
    
    # Get all users
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    print(f"Found {len(users)} users\n")
    
    for user in users:
        try:
            await train_rl_for_user(user.id, episodes=100)
        except Exception as e:
            print(f"❌ Error for user {user.id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ All RL models trained!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())