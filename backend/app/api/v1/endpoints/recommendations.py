"""
Recommendations endpoints - Using Reinforcement Learning
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import os
import sys

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UsageData, LifestylePattern, Recommendation
from pydantic import BaseModel

router = APIRouter()

# Import RL engine
try:
    from app.ml_engines.rl_recommendation_engine import RLRecommendationEngine, RecommendationAction
    RL_AVAILABLE = True
    print("✅ RL engine loaded successfully")
except ImportError as e:
    print(f"⚠️ RL engine not available: {str(e)}")
    print(f"   Falling back to static recommendations")
    RL_AVAILABLE = False
    # Create dummy classes so code doesn't break
    class RLRecommendationEngine:
        pass
    class RecommendationAction:
        ACTIONS = []

# Pydantic models for requests
class FeedbackRequest(BaseModel):
    recommendation_id: int
    accepted: bool
    implemented: bool = False
    rating: int = 3  # 1-5
    actual_savings_kwh: float = 0.0
    estimated_savings_kwh: float = 0.0
    time_to_implement_days: int = 0
    notes: str = ""


async def get_user_state_data(user_id: int, db: AsyncSession):
    """Get user data for RL state"""
    # Get user
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Get recent usage
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(UsageData)
        .filter(
            UsageData.user_id == user_id,
            UsageData.timestamp >= thirty_days_ago
        )
    )
    usage_records = result.scalars().all()
    
    if not usage_records:
        # Return defaults if no data
        return {
            'user_data': {
                'avg_daily_consumption': 10.0,
                'consumption_trend': 0.0,
                'has_ac': True,
                'house_size': 150,
                'occupants': 3,
                'bill_ratio': 1.0,
                'days_into_month': datetime.utcnow().day,
                'acceptance_rate': 0.5
            },
            'usage_data': {
                'hour': datetime.utcnow().hour,
                'is_weekend': datetime.utcnow().weekday() >= 5,
                'temperature': 25.0
            },
            'patterns': {}
        }
    
    # Calculate metrics
    total_consumption = sum(r.consumption_kwh for r in usage_records)
    days = len(set(r.timestamp.date() for r in usage_records))
    avg_daily = total_consumption / max(days, 1)
    
    # Get latest usage data
    latest = usage_records[0] if usage_records else None
    
    # Get patterns
    result = await db.execute(
        select(LifestylePattern).filter(LifestylePattern.user_id == user_id)
    )
    patterns = result.scalars().all()
    
    pattern_data = {
        'sleep_regularity': 0.5,
        'works_from_home': False,
        'weekend_spike': 0.0,
        'seasonality': 0.5
    }
    
    for p in patterns:
        if p.pattern_type == 'sleep_cycle':
            pattern_data['sleep_regularity'] = p.confidence
        elif p.pattern_type == 'work_hours':
            pattern_data['works_from_home'] = p.pattern_data.get('works_from_home', False)
        elif p.pattern_type == 'weekend_pattern':
            diff = p.pattern_data.get('difference_percentage', 0)
            pattern_data['weekend_spike'] = abs(diff) / 100.0
        elif p.pattern_type == 'seasonal_pattern':
            level = p.pattern_data.get('seasonality_level', 'medium')
            pattern_data['seasonality'] = 0.3 if level == 'low' else 0.7
    
    # Calculate acceptance rate from past recommendations
    result = await db.execute(
        select(Recommendation)
        .filter(Recommendation.user_id == user_id)
    )
    past_recs = result.scalars().all()
    
    if past_recs:
        accepted = sum(1 for r in past_recs if r.status == 'accepted')
        acceptance_rate = accepted / len(past_recs)
    else:
        acceptance_rate = 0.5
    
    return {
        'user_data': {
            'avg_daily_consumption': avg_daily,
            'consumption_trend': 0.0,
            'has_ac': True,
            'house_size': 150,
            'occupants': 3,
            'bill_ratio': 1.0,
            'days_into_month': datetime.utcnow().day,
            'acceptance_rate': acceptance_rate
        },
        'usage_data': {
            'hour': datetime.utcnow().hour,
            'is_weekend': datetime.utcnow().weekday() >= 5,
            'temperature': latest.temperature_celsius if latest else 25.0
        },
        'patterns': pattern_data
    }


def calculate_savings_amount(savings_kwh: float, tariff_rate: float = 6.0):
    """Calculate monetary savings from kWh savings"""
    return savings_kwh * tariff_rate * 30  # Monthly savings


@router.get("/active")
async def get_active_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered recommendations using RL"""
    
    # Check if RL model exists
    model_path = f"models/recommendation/user_{current_user.id}"
    use_rl = RL_AVAILABLE and os.path.exists(f"{model_path}/rl_model.h5")
    
    if use_rl:
        try:
            # Get user state data
            state_data = await get_user_state_data(current_user.id, db)
            
            if state_data:
                # Load RL engine
                engine = RLRecommendationEngine()
                loaded = engine.load(model_path)
                
                if loaded:
                    # Get state vector
                    state = engine.get_state(
                        state_data['user_data'],
                        state_data['usage_data'],
                        state_data['patterns']
                    )
                    
                    # Get RL recommendations
                    rl_recs = engine.get_recommendations(state, top_k=3)
                    
                    # Format for response
                    recommendations = []
                    for i, rec in enumerate(rl_recs, 1):
                        savings_amount = calculate_savings_amount(rec['estimated_savings_kwh'])
                        
                        recommendations.append({
                            "id": i,
                            "type": rec['action_id'],
                            "title": rec['title'],
                            "description": rec['description'],
                            "estimated_savings_kwh": round(rec['estimated_savings_kwh'], 2),
                            "estimated_savings_amount": round(savings_amount, 2),
                            "effort_level": rec['effort_level'],
                            "category": rec['category'],
                            "priority": i,
                            "source": "RL Engine",
                            "action_steps": get_action_steps(rec['action_id'])
                        })
                    
                    return recommendations
        except Exception as e:
            print(f"RL recommendation error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Fallback to static recommendations
    return get_static_recommendations()


def get_action_steps(action_id: str):
    """Get action steps for a recommendation"""
    steps_map = {
        'reduce_ac_temp': [
            "Set AC thermostat to 24°C instead of 22°C",
            "Use ceiling fans in combination with AC",
            "Clean AC filters monthly for efficiency"
        ],
        'led_upgrade': [
            "Identify all non-LED bulbs in your home",
            "Purchase LED replacements (check wattage)",
            "Install LEDs in most-used rooms first"
        ],
        'standby_power': [
            "Purchase smart power strips with auto-off",
            "Unplug chargers when not in use",
            "Turn off devices completely instead of standby"
        ],
        'optimize_fridge': [
            "Clean refrigerator coils at the back",
            "Check door seals for gaps",
            "Set temperature to 3-5°C for optimal efficiency"
        ],
        'water_heater_timer': [
            "Purchase a programmable timer switch",
            "Install on water heater circuit",
            "Program to heat water during usage hours only"
        ],
        'smart_thermostat': [
            "Research compatible smart thermostats",
            "Hire professional for installation",
            "Program schedules based on your routine"
        ],
        'shift_heavy_loads': [
            "Identify off-peak hours (usually 10 PM - 6 AM)",
            "Run washing machine/dryer during these hours",
            "Use delay start features on appliances"
        ],
        'insulation_upgrade': [
            "Add weather stripping to doors and windows",
            "Seal gaps around pipes and cables",
            "Consider attic insulation for long-term savings"
        ],
        'fan_instead_ac': [
            "Install ceiling fans in main rooms",
            "Use fans when temperature is below 28°C",
            "Combine fans with natural ventilation"
        ],
        'solar_investment': [
            "Get solar potential assessment for your roof",
            "Compare quotes from multiple installers",
            "Research government subsidies and incentives"
        ]
    }
    
    return steps_map.get(action_id, ["Implement this recommendation", "Monitor your savings", "Adjust as needed"])


def get_static_recommendations():
    """Fallback static recommendations"""
    return [
        {
            "id": 1,
            "type": "reduce_ac_temp",
            "title": "Reduce AC Temperature",
            "description": "Set your AC temperature to 24°C instead of 22°C to reduce energy consumption.",
            "estimated_savings_kwh": 1.5,
            "estimated_savings_amount": 270.0,
            "effort_level": "easy",
            "category": "cooling",
            "priority": 1,
            "source": "Static",
            "action_steps": get_action_steps('reduce_ac_temp')
        },
        {
            "id": 2,
            "type": "led_upgrade",
            "title": "Switch to LED Bulbs",
            "description": "Replace remaining incandescent bulbs with LED alternatives.",
            "estimated_savings_kwh": 2.0,
            "estimated_savings_amount": 360.0,
            "effort_level": "moderate",
            "category": "lighting",
            "priority": 2,
            "source": "Static",
            "action_steps": get_action_steps('led_upgrade')
        },
        {
            "id": 3,
            "type": "standby_power",
            "title": "Eliminate Standby Power",
            "description": "Use smart plugs to eliminate vampire power drain.",
            "estimated_savings_kwh": 0.6,
            "estimated_savings_amount": 108.0,
            "effort_level": "easy",
            "category": "devices",
            "priority": 3,
            "source": "Static",
            "action_steps": get_action_steps('standby_power')
        }
    ]


@router.post("/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a recommendation"""
    # Create or update recommendation record
    recommendation = Recommendation(
        user_id=current_user.id,
        recommendation_type="rl_generated",
        title=f"Recommendation {recommendation_id}",
        description="User accepted recommendation",
        estimated_savings_kwh=0.0,
        status="accepted",
        created_at=datetime.utcnow()
    )
    
    db.add(recommendation)
    await db.commit()
    
    return {
        "message": "Recommendation accepted",
        "recommendation_id": recommendation_id,
        "status": "accepted"
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on a recommendation for RL training"""
    
    # Update recommendation in database
    result = await db.execute(
        select(Recommendation).filter(
            Recommendation.id == feedback.recommendation_id,
            Recommendation.user_id == current_user.id
        )
    )
    recommendation = result.scalar_one_or_none()
    
    if recommendation:
        recommendation.status = "implemented" if feedback.implemented else "accepted"
        recommendation.user_rating = feedback.rating
        recommendation.actual_savings_kwh = feedback.actual_savings_kwh
        await db.commit()
    
    # Train RL model with feedback
    model_path = f"models/recommendation/user_{current_user.id}"
    
    if RL_AVAILABLE and os.path.exists(f"{model_path}/rl_model.h5"):
        try:
            # Get current state
            state_data = await get_user_state_data(current_user.id, db)
            
            if state_data:
                engine = RLRecommendationEngine()
                loaded = engine.load(model_path)
                
                if loaded:
                    # Get state
                    state = engine.get_state(
                        state_data['user_data'],
                        state_data['usage_data'],
                        state_data['patterns']
                    )
                    
                    # Calculate reward
                    feedback_dict = {
                        'accepted': feedback.accepted,
                        'implemented': feedback.implemented,
                        'rating': feedback.rating,
                        'actual_savings': feedback.actual_savings_kwh,
                        'estimated_savings': feedback.estimated_savings_kwh,
                        'time_to_implement': feedback.time_to_implement_days
                    }
                    
                    reward = engine.calculate_reward(feedback_dict)
                    
                    # Update model (online learning)
                    # Get next state (updated acceptance rate)
                    next_state = state.copy()
                    next_state[14] = (state[14] + (1.0 if feedback.accepted else 0.0)) / 2.0
                    
                    # Store experience
                    action_idx = feedback.recommendation_id - 1  # Approximate
                    engine.remember(state, action_idx, reward, next_state, False)
                    
                    # Train if enough experiences
                    if len(engine.memory) >= engine.batch_size:
                        engine.replay()
                        engine.save(model_path)
                    
                    print(f"✅ RL model updated with feedback (reward: {reward:.2f})")
        except Exception as e:
            print(f"RL feedback error: {str(e)}")
    
    return {
        "message": "Feedback received",
        "reward_calculated": True,
        "model_updated": True
    }


@router.get("/history")
async def get_recommendation_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recommendation history"""
    result = await db.execute(
        select(Recommendation)
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
    )
    
    recommendations = result.scalars().all()
    
    return [
        {
            "id": rec.id,
            "title": rec.title,
            "description": rec.description,
            "status": rec.status,
            "rating": rec.user_rating,
            "estimated_savings": rec.estimated_savings_kwh,
            "actual_savings": rec.actual_savings_kwh,
            "created_at": rec.created_at.isoformat()
        }
        for rec in recommendations
    ]


@router.get("/stats")
async def get_recommendation_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recommendation statistics"""
    result = await db.execute(
        select(Recommendation).filter(Recommendation.user_id == current_user.id)
    )
    recommendations = result.scalars().all()
    
    if not recommendations:
        return {
            "total_recommendations": 0,
            "accepted": 0,
            "implemented": 0,
            "acceptance_rate": 0.0,
            "implementation_rate": 0.0,
            "total_savings_kwh": 0.0,
            "average_rating": 0.0
        }
    
    accepted = sum(1 for r in recommendations if r.status in ['accepted', 'implemented'])
    implemented = sum(1 for r in recommendations if r.status == 'implemented')
    total_savings = sum(r.actual_savings_kwh or 0 for r in recommendations)
    ratings = [r.user_rating for r in recommendations if r.user_rating]
    
    return {
        "total_recommendations": len(recommendations),
        "accepted": accepted,
        "implemented": implemented,
        "acceptance_rate": round(accepted / len(recommendations) * 100, 1),
        "implementation_rate": round(implemented / len(recommendations) * 100, 1),
        "total_savings_kwh": round(total_savings, 2),
        "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0.0
    }