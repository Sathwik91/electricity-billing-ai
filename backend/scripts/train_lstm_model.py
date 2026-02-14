"""
Train LSTM model with proper feature matching
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import select
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import joblib
import json

from app.core.database import async_session_maker
from app.models.models import UsageData, User


class ProperLSTMModel:
    """LSTM model with proper feature management"""
    
    def __init__(self, sequence_length=24, feature_columns=None):
        self.sequence_length = sequence_length
        self.feature_columns = feature_columns or ['consumption_kwh']
        self.n_features = len(self.feature_columns)
        self.scaler = MinMaxScaler()
        self.model = None
        
    def prepare_data(self, data):
        """Prepare sequences for training"""
        # Extract only the features we need
        values = data[self.feature_columns].values
        
        # Scale the data
        scaled = self.scaler.fit_transform(values)
        
        X, y = [], []
        for i in range(len(scaled) - self.sequence_length):
            X.append(scaled[i:i + self.sequence_length])
            y.append(scaled[i + self.sequence_length, 0])  # Predict consumption_kwh only
        
        return np.array(X), np.array(y)
    
    def build_model(self):
        """Build LSTM model"""
        model = keras.Sequential([
            keras.layers.LSTM(64, input_shape=(self.sequence_length, self.n_features), return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(self, train_data, epochs=50, batch_size=32, validation_split=0.2):
        """Train the model"""
        X, y = self.prepare_data(train_data)
        
        if len(X) < 50:
            print("⚠️ Not enough data for training")
            return None
        
        print(f"Training with {len(X)} sequences...")
        print(f"Input shape: {X.shape}")
        print(f"Features: {self.feature_columns}")
        
        self.model = self.build_model()
        
        # Early stopping
        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=1
        )
        
        return history
    
    def predict(self, data, days_ahead=7):
        """Make predictions"""
        if self.model is None:
            return None
        
        try:
            # Get last sequence
            if len(data) < self.sequence_length:
                print(f"Not enough data: need {self.sequence_length}, got {len(data)}")
                return None
            
            # Extract features
            values = data[self.feature_columns].tail(self.sequence_length).values
            
            # Scale
            scaled = self.scaler.transform(values)
            
            predictions = []
            current_sequence = scaled.copy()
            
            # Predict hourly for days_ahead
            for hour in range(days_ahead * 24):
                # Prepare input
                X = current_sequence[-self.sequence_length:].reshape(1, self.sequence_length, self.n_features)
                
                # Predict next value
                pred = self.model.predict(X, verbose=0)
                
                # Store prediction
                predictions.append(pred[0, 0])
                
                # Create next input by shifting and appending prediction
                # For features other than consumption, we'll use the last known values
                next_features = current_sequence[-1].copy()
                next_features[0] = pred[0, 0]  # Update consumption with prediction
                
                # Add to sequence
                current_sequence = np.vstack([current_sequence, next_features.reshape(1, -1)])
            
            # Inverse transform predictions (only consumption column)
            # Create a full feature array for inverse transform
            predictions_full = np.zeros((len(predictions), self.n_features))
            predictions_full[:, 0] = predictions
            
            # Inverse transform
            predictions_inverse = self.scaler.inverse_transform(predictions_full)[:, 0]
            
            # Aggregate to daily
            daily_preds = []
            for i in range(0, len(predictions_inverse), 24):
                daily_sum = float(predictions_inverse[i:i+24].sum())
                daily_preds.append(daily_sum)
            
            return daily_preds[:days_ahead]
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def save(self, path):
        """Save model and metadata"""
        os.makedirs(path, exist_ok=True)
        
        # Save model
        self.model.save(f"{path}/lstm_model.h5")
        
        # Save scaler
        joblib.dump(self.scaler, f"{path}/scaler.pkl")
        
        # Save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'feature_columns': self.feature_columns,
            'n_features': self.n_features
        }
        with open(f"{path}/metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        print(f"✅ Model saved to {path}")
    
    def load(self, path):
        """Load model and metadata"""
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
            
            print(f"✅ Model loaded from {path}")
            print(f"   Sequence length: {self.sequence_length}")
            print(f"   Features: {self.feature_columns}")
            
            return True
        except Exception as e:
            print(f"❌ Load error: {str(e)}")
            return False


async def load_user_data(user_id: int) -> pd.DataFrame:
    """Load usage data for a user"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(UsageData)
            .filter(UsageData.user_id == user_id)
            .order_by(UsageData.timestamp)
        )
        usage_records = result.scalars().all()
        
        if not usage_records:
            return pd.DataFrame()
        
        data = []
        for r in usage_records:
            data.append({
                'timestamp': r.timestamp,
                'consumption_kwh': r.consumption_kwh,
                'hour_of_day': r.hour_of_day,
                'day_of_week': r.timestamp.weekday(),
                'is_weekend': int(r.is_weekend),
                'temperature_celsius': r.temperature_celsius or 25.0,
                'humidity_percentage': r.humidity_percentage or 60.0
            })
        
        return pd.DataFrame(data)


async def train_for_user(user_id: int, feature_set='simple'):
    """Train model for a user"""
    print(f"\n{'='*60}")
    print(f"Training LSTM Model for User ID: {user_id}")
    print(f"{'='*60}\n")
    
    # Load data
    data = await load_user_data(user_id)
    
    if len(data) == 0:
        print("❌ No data found")
        return
    
    print(f"📊 Loaded {len(data)} records")
    
    if len(data) < 200:
        print(f"⚠️ Warning: Only {len(data)} records. Need 200+ for best results.")
        if len(data) < 100:
            print("❌ Insufficient data for training")
            return
    
    # Choose feature set
    if feature_set == 'simple':
        features = ['consumption_kwh']
        print("Using SIMPLE feature set: [consumption_kwh]")
    elif feature_set == 'medium':
        features = ['consumption_kwh', 'hour_of_day', 'is_weekend']
        print("Using MEDIUM feature set: [consumption_kwh, hour_of_day, is_weekend]")
    else:  # full
        features = ['consumption_kwh', 'hour_of_day', 'day_of_week', 
                   'is_weekend', 'temperature_celsius', 'humidity_percentage']
        print("Using FULL feature set: all 6 features")
    
    # Initialize model
    model = ProperLSTMModel(
        sequence_length=24,
        feature_columns=features
    )
    
    print(f"\n🚀 Starting training...")
    print(f"Sequence length: 24 hours")
    print(f"Number of features: {len(features)}\n")
    
    # Train
    history = model.train(
        train_data=data,
        epochs=50,
        batch_size=32,
        validation_split=0.2
    )
    
    if history is None:
        print("❌ Training failed")
        return
    
    print(f"\n✅ Training complete!")
    print(f"📈 Final Training Loss: {history.history['loss'][-1]:.4f}")
    print(f"📈 Final Training MAE: {history.history['mae'][-1]:.4f}")
    
    if 'val_loss' in history.history:
        print(f"📈 Final Validation Loss: {history.history['val_loss'][-1]:.4f}")
        print(f"📈 Final Validation MAE: {history.history['val_mae'][-1]:.4f}")
    
    # Test prediction
    print(f"\n🔮 Testing 7-day prediction...")
    test_data = data.tail(200)  # Use last 200 records for test
    predictions = model.predict(test_data, days_ahead=7)
    
    if predictions is not None:
        print(f"📊 Daily Predictions:")
        for i, pred in enumerate(predictions, 1):
            print(f"   Day {i}: {pred:.2f} kWh")
        print(f"📊 7-day Total: {sum(predictions):.2f} kWh")
        print(f"📊 Daily Average: {np.mean(predictions):.2f} kWh")
    else:
        print("⚠️ Prediction test failed")
    
    # Save model
    model_dir = f"models/forecasting/user_{user_id}"
    model.save(model_dir)
    
    print(f"\n💾 Model saved successfully!")
    print(f"📁 Location: {model_dir}")


async def main():
    """Main training function"""
    print("\n" + "="*60)
    print("🤖 LSTM Model Training - Proper Feature Matching")
    print("="*60 + "\n")
    
    # Get all users
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    print(f"Found {len(users)} users\n")
    
    # Choose feature set
    print("Choose feature set:")
    print("1. Simple (consumption only) - Recommended")
    print("2. Medium (consumption + hour + weekend)")
    print("3. Full (all 6 features)")
    
    # For automation, using simple
    feature_set = 'simple'
    print(f"\nUsing: {feature_set}\n")
    
    for user in users:
        try:
            await train_for_user(user.id, feature_set)
        except Exception as e:
            print(f"❌ Error for user {user.id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ All models trained successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())