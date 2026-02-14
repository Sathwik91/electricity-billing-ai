"""
LSTM-based Bill Forecasting Model
Predicts monthly electricity consumption and bills using time-series deep learning
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BillForecastingModel:
    """
    LSTM-based forecasting model for electricity bill prediction
    """
    
    def __init__(
        self,
        sequence_length: int = 30,
        features: List[str] = None,
        model_path: str = "models/forecasting/"
    ):
        self.sequence_length = sequence_length
        self.features = features or [
            'consumption_kwh', 'hour_of_day', 'day_of_week', 
            'is_weekend', 'temperature_celsius', 'humidity_percentage'
        ]
        self.model_path = model_path
        
        self.model: Optional[keras.Model] = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM model architecture
        
        Args:
            input_shape: (sequence_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        model = keras.Sequential([
            # First LSTM layer with return sequences
            keras.layers.LSTM(
                128,
                return_sequences=True,
                input_shape=input_shape,
                dropout=0.2,
                recurrent_dropout=0.2
            ),
            keras.layers.BatchNormalization(),
            
            # Second LSTM layer
            keras.layers.LSTM(64, return_sequences=True, dropout=0.2),
            keras.layers.BatchNormalization(),
            
            # Third LSTM layer
            keras.layers.LSTM(32, dropout=0.2),
            keras.layers.BatchNormalization(),
            
            # Dense layers
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            
            # Output layer
            keras.layers.Dense(1, activation='linear')
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='huber',  # Robust to outliers
            metrics=['mae', 'mse']
        )
        
        return model
    
    def prepare_sequences(
        self,
        data: pd.DataFrame,
        target_col: str = 'consumption_kwh'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequential data for LSTM training
        
        Args:
            data: DataFrame with time-series features
            target_col: Target column name
            
        Returns:
            X, y arrays for training
        """
        # Select features
        feature_data = data[self.features].values
        target_data = data[target_col].values
        
        # Normalize features
        scaled_features = self.scaler.fit_transform(feature_data)
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_features) - self.sequence_length):
            X.append(scaled_features[i:i + self.sequence_length])
            y.append(target_data[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        train_data: pd.DataFrame,
        val_data: Optional[pd.DataFrame] = None,
        epochs: int = 100,
        batch_size: int = 32,
        early_stopping_patience: int = 10
    ) -> Dict[str, any]:
        """
        Train the forecasting model
        
        Args:
            train_data: Training dataset
            val_data: Validation dataset
            epochs: Number of training epochs
            batch_size: Training batch size
            early_stopping_patience: Patience for early stopping
            
        Returns:
            Training history and metrics
        """
        logger.info("Preparing training data...")
        X_train, y_train = self.prepare_sequences(train_data)
        
        validation_data = None
        if val_data is not None:
            X_val, y_val = self.prepare_sequences(val_data)
            validation_data = (X_val, y_val)
        
        # Build model
        logger.info(f"Building LSTM model with input shape: {X_train.shape[1:]}")
        self.model = self.build_model(X_train.shape[1:])
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if validation_data else 'loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                f"{self.model_path}/best_model.h5",
                monitor='val_loss' if validation_data else 'loss',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # Train model
        logger.info("Training model...")
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        
        # Calculate metrics
        train_metrics = self.evaluate(train_data)
        val_metrics = self.evaluate(val_data) if val_data is not None else {}
        
        logger.info(f"Training complete. Train MAE: {train_metrics['mae']:.2f}")
        if val_metrics:
            logger.info(f"Validation MAE: {val_metrics['mae']:.2f}")
        
        return {
            'history': history.history,
            'train_metrics': train_metrics,
            'val_metrics': val_metrics
        }
    
    def predict(
        self,
        data: pd.DataFrame,
        days_ahead: int = 30
    ) -> Dict[str, any]:
        """
        Predict future consumption
        
        Args:
            data: Recent historical data
            days_ahead: Number of days to forecast
            
        Returns:
            Predictions with confidence intervals
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before prediction")
        
        # Prepare last sequence
        feature_data = data[self.features].tail(self.sequence_length).values
        scaled_features = self.scaler.transform(feature_data)
        
        # Make predictions
        predictions = []
        current_sequence = scaled_features.copy()
        
        for _ in range(days_ahead):
            # Reshape for prediction
            X = current_sequence.reshape(1, self.sequence_length, len(self.features))
            
            # Predict next value
            pred = self.model.predict(X, verbose=0)[0][0]
            predictions.append(pred)
            
            # Update sequence (simplified - in production, update all features)
            new_row = current_sequence[-1].copy()
            new_row[0] = self.scaler.transform([[pred] + [0] * (len(self.features) - 1)])[0][0]
            current_sequence = np.vstack([current_sequence[1:], new_row])
        
        # Calculate confidence intervals (using prediction std)
        predictions_array = np.array(predictions)
        std = np.std(predictions_array)
        
        return {
            'predictions': predictions_array.tolist(),
            'mean': float(np.mean(predictions_array)),
            'total': float(np.sum(predictions_array)),
            'confidence_interval': {
                'lower': (predictions_array - 1.96 * std).tolist(),
                'upper': (predictions_array + 1.96 * std).tolist()
            }
        }
    
    def predict_monthly_bill(
        self,
        current_month_data: pd.DataFrame,
        remaining_days: int,
        tariff_slabs: Dict[str, float],
        fixed_charge: float = 50.0
    ) -> Dict[str, any]:
        """
        Predict end-of-month bill
        
        Args:
            current_month_data: Current month's usage data
            remaining_days: Days remaining in billing cycle
            tariff_slabs: Electricity tariff structure
            fixed_charge: Monthly fixed charge
            
        Returns:
            Bill prediction with breakdown
        """
        # Get current month consumption
        current_consumption = current_month_data['consumption_kwh'].sum()
        
        # Predict remaining consumption
        if remaining_days > 0:
            future_pred = self.predict(current_month_data, days_ahead=remaining_days)
            predicted_remaining = future_pred['total']
        else:
            predicted_remaining = 0
        
        # Total predicted consumption
        total_consumption = current_consumption + predicted_remaining
        
        # Calculate bill based on tariff slabs
        bill_amount = self._calculate_bill(total_consumption, tariff_slabs, fixed_charge)
        
        # Calculate confidence
        confidence = self._calculate_confidence(current_month_data)
        
        return {
            'predicted_consumption_kwh': float(total_consumption),
            'current_consumption_kwh': float(current_consumption),
            'predicted_remaining_kwh': float(predicted_remaining),
            'predicted_bill_amount': float(bill_amount),
            'fixed_charge': float(fixed_charge),
            'confidence_score': float(confidence),
            'days_remaining': remaining_days,
            'tariff_breakdown': self._get_tariff_breakdown(
                total_consumption, tariff_slabs
            )
        }
    
    def _calculate_bill(
        self,
        consumption_kwh: float,
        tariff_slabs: Dict[str, float],
        fixed_charge: float
    ) -> float:
        """Calculate bill amount based on slab rates"""
        bill = fixed_charge
        remaining_kwh = consumption_kwh
        
        # Sort slabs
        slabs = []
        for slab_range, rate in tariff_slabs.items():
            if '-' in slab_range:
                lower, upper = map(int, slab_range.split('-'))
                slabs.append((lower, upper, rate))
            elif '+' in slab_range:
                lower = int(slab_range.replace('+', ''))
                slabs.append((lower, float('inf'), rate))
        
        slabs.sort(key=lambda x: x[0])
        
        # Calculate bill
        for lower, upper, rate in slabs:
            if remaining_kwh <= 0:
                break
            
            slab_size = upper - lower + 1 if upper != float('inf') else remaining_kwh
            units_in_slab = min(remaining_kwh, slab_size)
            
            bill += units_in_slab * rate
            remaining_kwh -= units_in_slab
        
        return bill
    
    def _get_tariff_breakdown(
        self,
        consumption_kwh: float,
        tariff_slabs: Dict[str, float]
    ) -> List[Dict]:
        """Get detailed tariff breakdown"""
        breakdown = []
        remaining_kwh = consumption_kwh
        
        slabs = []
        for slab_range, rate in tariff_slabs.items():
            if '-' in slab_range:
                lower, upper = map(int, slab_range.split('-'))
                slabs.append((slab_range, lower, upper, rate))
            elif '+' in slab_range:
                lower = int(slab_range.replace('+', ''))
                slabs.append((slab_range, lower, float('inf'), rate))
        
        slabs.sort(key=lambda x: x[1])
        
        for slab_range, lower, upper, rate in slabs:
            if remaining_kwh <= 0:
                break
            
            slab_size = upper - lower + 1 if upper != float('inf') else remaining_kwh
            units_in_slab = min(remaining_kwh, slab_size)
            
            breakdown.append({
                'slab': slab_range,
                'units': float(units_in_slab),
                'rate': float(rate),
                'amount': float(units_in_slab * rate)
            })
            
            remaining_kwh -= units_in_slab
        
        return breakdown
    
    def _calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate prediction confidence based on data quality and quantity"""
        # Factor 1: Data quantity
        data_quantity_score = min(len(data) / 100, 1.0)
        
        # Factor 2: Data consistency (low variance in recent predictions)
        recent_data = data.tail(7)
        if len(recent_data) > 0:
            cv = recent_data['consumption_kwh'].std() / (recent_data['consumption_kwh'].mean() + 1e-6)
            consistency_score = max(0, 1 - cv)
        else:
            consistency_score = 0.5
        
        # Weighted average
        confidence = 0.6 * data_quantity_score + 0.4 * consistency_score
        
        return min(max(confidence, 0.0), 1.0)
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, float]:
        """Evaluate model performance"""
        X, y_true = self.prepare_sequences(data)
        y_pred = self.model.predict(X, verbose=0).flatten()
        
        return {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'r2': float(r2_score(y_true, y_pred)),
            'mape': float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100)
        }
    
    def save(self, path: str = None):
        """Save model and scaler"""
        path = path or self.model_path
        self.model.save(f"{path}/lstm_model.h5")
        joblib.dump(self.scaler, f"{path}/scaler.pkl")
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str = None):
        """Load model and scaler"""
        path = path or self.model_path
        self.model = keras.models.load_model(f"{path}/lstm_model.h5")
        self.scaler = joblib.load(f"{path}/scaler.pkl")
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
