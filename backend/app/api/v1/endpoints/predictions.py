"""
Predictions endpoints - Using Properly Trained LSTM
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import calendar
import os
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UsageData
from app.core.config import settings
from app.integrations.factory import ProviderFactory

router = APIRouter()

# Import LSTM components
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import joblib
import json

# Add at the top of the file after imports
from functools import lru_cache

# Cache loaded models
_model_cache = {}

def get_cached_lstm_model(user_id: int, model_path: str):
    """Get or load LSTM model from cache"""
    if user_id not in _model_cache:
        model = ProperLSTMModel()
        loaded = model.load(model_path)
        if loaded:
            _model_cache[user_id] = model
        else:
            return None
    return _model_cache.get(user_id)


class ProperLSTMModel:
    """LSTM model with proper feature management - for prediction"""
    
    def __init__(self):
        self.sequence_length = 24
        self.feature_columns = ['consumption_kwh']
        self.n_features = 1
        self.scaler = None
        self.model = None
        
    def predict(self, data, days_ahead=7):
        """Make predictions"""
        if self.model is None:
            return None
        
        try:
            if len(data) < self.sequence_length:
                return None
            
            # Extract features
            values = data[self.feature_columns].tail(self.sequence_length).values
            
            # Scale
            scaled = self.scaler.transform(values)
            
            predictions = []
            current_sequence = scaled.copy()
            
            # Predict hourly
            for _ in range(days_ahead * 24):
                X = current_sequence[-self.sequence_length:].reshape(1, self.sequence_length, self.n_features)
                pred = self.model.predict(X, verbose=0)
                predictions.append(pred[0, 0])
                
                # Update sequence
                next_features = current_sequence[-1].copy()
                next_features[0] = pred[0, 0]
                current_sequence = np.vstack([current_sequence, next_features.reshape(1, -1)])
            
            # Inverse transform
            predictions_full = np.zeros((len(predictions), self.n_features))
            predictions_full[:, 0] = predictions
            predictions_inverse = self.scaler.inverse_transform(predictions_full)[:, 0]
            
            # Aggregate to daily
            daily_preds = []
            for i in range(0, len(predictions_inverse), 24):
                daily_sum = float(predictions_inverse[i:i+24].sum())
                daily_preds.append(daily_sum)
            
            return daily_preds[:days_ahead]
            
        except Exception as e:
            print(f"LSTM predict error: {str(e)}")
            return None
    
    def load(self, path):
        """Load model"""
        try:
            # Load metadata
            with open(f"{path}/metadata.json", 'r') as f:
                metadata = json.load(f)
            
            self.sequence_length = metadata['sequence_length']
            self.feature_columns = metadata['feature_columns']
            self.n_features = metadata['n_features']
            
            # Load model and scaler
            self.model = keras.models.load_model(f"{path}/lstm_model.h5")
            self.scaler = joblib.load(f"{path}/scaler.pkl")
            
            return True
        except Exception as e:
            print(f"LSTM load error: {str(e)}")
            return False


@router.get("/current-month")
async def get_current_month_prediction(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current month bill prediction using real or simulated tariff."""
    
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day
    days_remaining = days_in_month - days_elapsed
    
    result = await db.execute(
        select(func.sum(UsageData.consumption_kwh))
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= month_start,
            UsageData.timestamp <= now
        )
    )
    current_consumption = float(result.scalar() or 0)
    
    model_path = f"models/forecasting/user_{current_user.id}"
    use_lstm = os.path.exists(f"{model_path}/lstm_model.h5") and os.path.exists(f"{model_path}/metadata.json")
    
    if use_lstm and days_remaining > 0:
        try:
            result = await db.execute(
                select(UsageData)
                .filter(UsageData.user_id == current_user.id)
                .order_by(UsageData.timestamp.desc())
                .limit(200)
            )
            records = result.scalars().all()
            
            if len(records) >= 100:
                data = pd.DataFrame([{
                    'timestamp': r.timestamp,
                    'consumption_kwh': r.consumption_kwh,
                    'hour_of_day': r.hour_of_day,
                    'day_of_week': r.timestamp.weekday(),
                    'is_weekend': int(r.is_weekend),
                    'temperature_celsius': r.temperature_celsius or 25.0,
                    'humidity_percentage': r.humidity_percentage or 60.0
                } for r in reversed(records)])
                
                model = get_cached_lstm_model(current_user.id, model_path)
                
                if model:
                    predictions = model.predict(data, days_ahead=days_remaining)
                    
                    if predictions is not None and len(predictions) > 0:
                        predicted_remaining = sum(predictions)
                        method = "LSTM Neural Network"
                    else:
                        daily_avg = current_consumption / days_elapsed if days_elapsed > 0 else 0
                        predicted_remaining = daily_avg * days_remaining
                        method = "Simple Average (LSTM prediction failed)"
                else:
                    daily_avg = current_consumption / days_elapsed if days_elapsed > 0 else 0
                    predicted_remaining = daily_avg * days_remaining
                    method = "Simple Average (model load failed)"
            else:
                daily_avg = current_consumption / days_elapsed if days_elapsed > 0 else 0
                predicted_remaining = daily_avg * days_remaining
                method = "Simple Average (insufficient data)"
                
        except Exception:
            daily_avg = current_consumption / days_elapsed if days_elapsed > 0 else 0
            predicted_remaining = daily_avg * days_remaining
            method = "Simple Average (exception)"
    else:
        daily_avg = current_consumption / days_elapsed if days_elapsed > 0 else 0
        predicted_remaining = daily_avg * days_remaining
        method = "Simple Average"
    
    total_predicted_consumption = current_consumption + predicted_remaining

    tariff_provider = ProviderFactory.get_tariff_provider()
    region = os.getenv("DEFAULT_REGION", "Karnataka")

    try:
        tariff = await tariff_provider.get_current_tariff(region)
        bill_info = await tariff_provider.calculate_bill(
            total_predicted_consumption,
            tariff
        )
        predicted_bill = bill_info["total_amount"]
        fixed_charge = bill_info.get("fixed_charge", settings.FIXED_CHARGE)
    except Exception:
        predicted_bill = calculate_bill(total_predicted_consumption)
        fixed_charge = settings.FIXED_CHARGE

    if now.month == 1:
        prev_month = 12
        prev_year = now.year - 1
    else:
        prev_month = now.month - 1
        prev_year = now.year
    
    prev_month_start = datetime(prev_year, prev_month, 1)
    prev_month_end = datetime(now.year, now.month, 1) - timedelta(days=1)
    
    result = await db.execute(
        select(func.sum(UsageData.consumption_kwh))
        .filter(
            UsageData.user_id == current_user.id,
            UsageData.timestamp >= prev_month_start,
            UsageData.timestamp <= prev_month_end
        )
    )
    previous_consumption = float(result.scalar() or 0)

    try:
        tariff = await tariff_provider.get_current_tariff(region)
        bill_info = await tariff_provider.calculate_bill(
            previous_consumption,
            tariff
        )
        previous_bill = bill_info["total_amount"]
    except Exception:
        previous_bill = calculate_bill(previous_consumption)

    percentage_change = (
        (predicted_bill - previous_bill) / previous_bill * 100
        if previous_bill > 0 else 0
    )

    return {
        "predicted_consumption_kwh": round(total_predicted_consumption, 2),
        "current_consumption_kwh": round(current_consumption, 2),
        "predicted_remaining_kwh": round(predicted_remaining, 2),
        "predicted_bill_amount": round(predicted_bill, 2),
        "previous_month_bill": round(previous_bill, 2),
        "percentage_change": round(percentage_change, 2),
        "confidence_score": min(days_elapsed / days_in_month, 0.95),
        "days_remaining": days_remaining,
        "days_elapsed": days_elapsed,
        "fixed_charge": fixed_charge,
        "currency": settings.DEFAULT_CURRENCY,
        "prediction_method": method,
        "lstm_available": use_lstm
    }


def calculate_bill(consumption_kwh: float) -> float:
    """Calculate bill"""
    bill = settings.FIXED_CHARGE
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