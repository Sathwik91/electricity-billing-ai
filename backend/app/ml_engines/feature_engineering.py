"""
Advanced feature engineering for electricity prediction
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple


class AdvancedFeatureEngineering:
    """Create sophisticated features for better predictions"""
    
    def __init__(self):
        self.scaler_mean = None
        self.scaler_std = None
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive time-based features"""
        df = df.copy()
        
        # Basic time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        df['month'] = df['timestamp'].dt.month
        df['quarter'] = df['timestamp'].dt.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Cyclical encoding (important for time series!)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Time of day categories
        df['time_of_day'] = pd.cut(
            df['hour'],
            bins=[0, 6, 12, 18, 24],
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        )
        
        # Working hours
        df['is_working_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17) & (df['day_of_week'] < 5)).astype(int)
        
        # Peak hours (high electricity usage)
        df['is_peak_hours'] = ((df['hour'] >= 17) & (df['hour'] <= 22)).astype(int)
        
        # Holiday indicator (can be enhanced with actual holiday calendar)
        df['is_month_start'] = (df['day_of_month'] <= 5).astype(int)
        df['is_month_end'] = (df['day_of_month'] >= 25).astype(int)
        
        return df
    
    def create_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 24, 168]) -> pd.DataFrame:
        """Create lagged consumption features"""
        df = df.copy()
        
        for lag in lags:
            df[f'consumption_lag_{lag}'] = df['consumption_kwh'].shift(lag)
        
        return df
    
    def create_rolling_features(self, df: pd.DataFrame, windows: List[int] = [6, 12, 24, 168]) -> pd.DataFrame:
        """Create rolling statistics"""
        df = df.copy()
        
        for window in windows:
            # Rolling mean
            df[f'consumption_rolling_mean_{window}'] = df['consumption_kwh'].rolling(window=window, min_periods=1).mean()
            
            # Rolling std
            df[f'consumption_rolling_std_{window}'] = df['consumption_kwh'].rolling(window=window, min_periods=1).std()
            
            # Rolling min/max
            df[f'consumption_rolling_min_{window}'] = df['consumption_kwh'].rolling(window=window, min_periods=1).min()
            df[f'consumption_rolling_max_{window}'] = df['consumption_kwh'].rolling(window=window, min_periods=1).max()
            
            # Rate of change
            df[f'consumption_change_{window}'] = df['consumption_kwh'].pct_change(periods=window)
        
        return df
    
    def create_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced weather features"""
        df = df.copy()
        
        if 'temperature_celsius' in df.columns:
            # Temperature bins
            df['temp_category'] = pd.cut(
                df['temperature_celsius'],
                bins=[0, 20, 25, 30, 50],
                labels=['cold', 'moderate', 'warm', 'hot']
            )
            
            # Temperature squared (AC usage increases non-linearly)
            df['temp_squared'] = df['temperature_celsius'] ** 2
            
            # Cooling degree days
            df['cooling_degree_days'] = np.maximum(df['temperature_celsius'] - 24, 0)
            
            # Heating degree days
            df['heating_degree_days'] = np.maximum(18 - df['temperature_celsius'], 0)
        
        if 'humidity_percentage' in df.columns:
            # Humidity squared
            df['humidity_squared'] = df['humidity_percentage'] ** 2
            
            # Heat index (feels like temperature)
            if 'temperature_celsius' in df.columns:
                df['heat_index'] = self._calculate_heat_index(
                    df['temperature_celsius'], 
                    df['humidity_percentage']
                )
        
        return df
    
    def _calculate_heat_index(self, temp: pd.Series, humidity: pd.Series) -> pd.Series:
        """Calculate heat index (feels like temperature)"""
        # Simplified heat index formula
        hi = (0.5 * (temp + 61.0 + ((temp - 68.0) * 1.2) + (humidity * 0.094)))
        return hi
    
    def create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create statistical features per user"""
        df = df.copy()
        
        # Groupby hour statistics
        hourly_stats = df.groupby('hour')['consumption_kwh'].agg(['mean', 'std', 'median'])
        df = df.merge(
            hourly_stats.add_prefix('hour_'),
            left_on='hour',
            right_index=True,
            how='left'
        )
        
        # Groupby day of week statistics
        dow_stats = df.groupby('day_of_week')['consumption_kwh'].agg(['mean', 'std', 'median'])
        df = df.merge(
            dow_stats.add_prefix('dow_'),
            left_on='day_of_week',
            right_index=True,
            how='left'
        )
        
        # Deviation from hourly average
        df['deviation_from_hour_avg'] = df['consumption_kwh'] - df['hour_mean']
        
        # Z-score (standardized consumption)
        overall_mean = df['consumption_kwh'].mean()
        overall_std = df['consumption_kwh'].std()
        df['consumption_zscore'] = (df['consumption_kwh'] - overall_mean) / overall_std
        
        return df
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature engineering"""
        print("Creating time features...")
        df = self.create_time_features(df)
        
        print("Creating lag features...")
        df = self.create_lag_features(df)
        
        print("Creating rolling features...")
        df = self.create_rolling_features(df)
        
        print("Creating weather features...")
        df = self.create_weather_features(df)
        
        print("Creating statistical features...")
        df = self.create_statistical_features(df)
        
        # Fill NaN values created by rolling/lag
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        return df
    
    def normalize_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Normalize numerical features"""
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        numerical_cols = [col for col in numerical_cols if col != 'consumption_kwh']
        
        if fit:
            self.scaler_mean = df[numerical_cols].mean()
            self.scaler_std = df[numerical_cols].std()
        
        df[numerical_cols] = (df[numerical_cols] - self.scaler_mean) / (self.scaler_std + 1e-8)
        
        return df


# Helper function
def prepare_enhanced_data(user_id: int, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare data with all enhancements"""
    fe = AdvancedFeatureEngineering()
    
    # Apply all feature engineering
    df_enhanced = fe.create_all_features(df)
    
    # Normalize
    df_enhanced = fe.normalize_features(df_enhanced, fit=True)
    
    # Select features for model
    feature_cols = [col for col in df_enhanced.columns if col not in ['timestamp', 'consumption_kwh']]
    
    X = df_enhanced[feature_cols].values
    y = df_enhanced['consumption_kwh'].values
    
    return X, y, feature_cols