"""
Lifestyle Pattern Learning Module
Detects and learns user behavior patterns from electricity usage
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
from datetime import datetime, time
import joblib
import logging

logger = logging.getLogger(__name__)


class LifestylePatternLearner:
    """
    Learns lifestyle patterns from electricity usage data
    """
    
    def __init__(self, model_path: str = "models/patterns/"):
        self.model_path = model_path
        self.scaler = StandardScaler()
        self.kmeans_model = None
        self.behavioral_clusters = None
        self.patterns = {}
        
    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for pattern learning
        
        Args:
            data: Usage data with timestamp and consumption
            
        Returns:
            DataFrame with extracted features
        """
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        features = pd.DataFrame(index=df.index)
        
        # Temporal features
        features['hour'] = df.index.hour
        features['day_of_week'] = df.index.dayofweek
        features['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
        features['month'] = df.index.month
        features['week_of_year'] = df.index.isocalendar().week
        
        # Consumption features
        features['consumption'] = df['consumption_kwh']
        features['consumption_log'] = np.log1p(df['consumption_kwh'])
        
        # Rolling statistics (24-hour window)
        features['consumption_rolling_mean'] = df['consumption_kwh'].rolling(24, min_periods=1).mean()
        features['consumption_rolling_std'] = df['consumption_kwh'].rolling(24, min_periods=1).std()
        features['consumption_rolling_max'] = df['consumption_kwh'].rolling(24, min_periods=1).max()
        
        # Hour-level aggregations
        hourly_avg = df.groupby(df.index.hour)['consumption_kwh'].mean()
        features['hour_avg_consumption'] = features['hour'].map(hourly_avg)
        
        # Day-level aggregations
        daily_avg = df.groupby(df.index.dayofweek)['consumption_kwh'].mean()
        features['day_avg_consumption'] = features['day_of_week'].map(daily_avg)
        
        # Peak vs off-peak
        features['is_peak_hour'] = ((features['hour'] >= 18) & (features['hour'] <= 22)).astype(int)
        
        return features.fillna(0)
    
    def detect_sleep_cycle(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Detect user's sleep cycle from low consumption patterns
        
        Args:
            data: Hourly usage data
            
        Returns:
            Sleep cycle information
        """
        hourly_avg = data.groupby(data['timestamp'].dt.hour)['consumption_kwh'].mean()
        
        # Find consecutive low-consumption hours (below 25th percentile)
        threshold = hourly_avg.quantile(0.25)
        low_hours = hourly_avg[hourly_avg <= threshold].index.tolist()
        
        # Find longest consecutive sequence
        if not low_hours:
            return {'detected': False}
        
        sequences = []
        current_seq = [low_hours[0]]
        
        for i in range(1, len(low_hours)):
            if low_hours[i] == (low_hours[i-1] + 1) % 24:
                current_seq.append(low_hours[i])
            else:
                sequences.append(current_seq)
                current_seq = [low_hours[i]]
        sequences.append(current_seq)
        
        # Get longest sequence
        sleep_hours = max(sequences, key=len)
        
        return {
            'detected': True,
            'sleep_start_hour': sleep_hours[0],
            'sleep_end_hour': (sleep_hours[-1] + 1) % 24,
            'sleep_duration_hours': len(sleep_hours),
            'average_sleep_consumption': float(hourly_avg[sleep_hours].mean()),
            'confidence': len(sleep_hours) / 8  # Assuming 8 hours ideal sleep
        }
    
    def detect_work_hours(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Detect work hours from weekday consumption patterns
        
        Args:
            data: Usage data
            
        Returns:
            Work hours information
        """
        # Filter weekdays only
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        weekday_data = data[data['timestamp'].dt.dayofweek < 5].copy()
        
        if len(weekday_data) == 0:
            return {'detected': False}
        
        # Get hourly average for weekdays
        hourly_avg = weekday_data.groupby(
            weekday_data['timestamp'].dt.hour
        )['consumption_kwh'].mean()
        
        # Work hours typically show reduced consumption (9 AM - 5 PM)
        daytime_hours = list(range(9, 18))
        daytime_consumption = hourly_avg[daytime_hours]
        
        # Compare with morning/evening
        morning_consumption = hourly_avg[list(range(6, 9))].mean()
        evening_consumption = hourly_avg[list(range(18, 22))].mean()
        
        # If daytime is significantly lower, likely working outside
        avg_daytime = daytime_consumption.mean()
        threshold = 0.7 * min(morning_consumption, evening_consumption)
        
        works_outside = avg_daytime < threshold
        
        if works_outside:
            # Find actual low consumption hours during daytime
            low_hours = daytime_consumption[
                daytime_consumption < daytime_consumption.median()
            ].index.tolist()
            
            work_start = min(low_hours) if low_hours else 9
            work_end = max(low_hours) + 1 if low_hours else 17
        else:
            work_start = None
            work_end = None
        
        return {
            'detected': True,
            'works_from_home': not works_outside,
            'work_start_hour': work_start,
            'work_end_hour': work_end,
            'avg_weekday_consumption': float(weekday_data['consumption_kwh'].mean()),
            'avg_daytime_consumption': float(avg_daytime),
            'confidence': 0.8 if abs(avg_daytime - threshold) > 0.3 else 0.6
        }
    
    def detect_weekend_pattern(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Detect weekend vs weekday behavior
        
        Args:
            data: Usage data
            
        Returns:
            Weekend pattern information
        """
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        weekday_data = data[data['timestamp'].dt.dayofweek < 5]
        weekend_data = data[data['timestamp'].dt.dayofweek >= 5]
        
        if len(weekday_data) == 0 or len(weekend_data) == 0:
            return {'detected': False}
        
        weekday_avg = weekday_data['consumption_kwh'].mean()
        weekend_avg = weekend_data['consumption_kwh'].mean()
        
        # Statistical test for difference
        t_stat, p_value = stats.ttest_ind(
            weekday_data['consumption_kwh'],
            weekend_data['consumption_kwh']
        )
        
        difference_pct = ((weekend_avg - weekday_avg) / weekday_avg) * 100
        
        # Hourly patterns
        weekday_hourly = weekday_data.groupby(
            weekday_data['timestamp'].dt.hour
        )['consumption_kwh'].mean()
        weekend_hourly = weekend_data.groupby(
            weekend_data['timestamp'].dt.hour
        )['consumption_kwh'].mean()
        
        return {
            'detected': True,
            'weekend_avg_consumption': float(weekend_avg),
            'weekday_avg_consumption': float(weekday_avg),
            'difference_percentage': float(difference_pct),
            'statistically_significant': p_value < 0.05,
            'p_value': float(p_value),
            'weekend_peak_hour': int(weekend_hourly.idxmax()),
            'weekday_peak_hour': int(weekday_hourly.idxmax()),
            'pattern_type': self._classify_weekend_pattern(difference_pct)
        }
    
    def _classify_weekend_pattern(self, diff_pct: float) -> str:
        """Classify weekend pattern type"""
        if diff_pct > 20:
            return "high_weekend_usage"
        elif diff_pct < -20:
            return "low_weekend_usage"
        else:
            return "consistent_usage"
    
    def detect_seasonal_patterns(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Detect seasonal consumption patterns
        
        Args:
            data: Usage data spanning multiple months
            
        Returns:
            Seasonal pattern information
        """
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Group by month
        monthly_avg = data.groupby(data['timestamp'].dt.month)['consumption_kwh'].agg([
            'mean', 'std', 'count'
        ])
        
        if len(monthly_avg) < 3:
            return {'detected': False, 'reason': 'insufficient_data'}
        
        # Identify peak and low months
        peak_month = monthly_avg['mean'].idxmax()
        low_month = monthly_avg['mean'].idxmin()
        
        # Calculate seasonal variation
        seasonal_range = monthly_avg['mean'].max() - monthly_avg['mean'].min()
        avg_consumption = monthly_avg['mean'].mean()
        variation_pct = (seasonal_range / avg_consumption) * 100
        
        # Classify season pattern
        if variation_pct > 30:
            seasonality = "high"
        elif variation_pct > 15:
            seasonality = "moderate"
        else:
            seasonality = "low"
        
        # Detect summer AC usage (higher consumption in summer months 4-9)
        summer_months = [4, 5, 6, 7, 8, 9]
        if set(summer_months).issubset(set(monthly_avg.index)):
            summer_avg = monthly_avg.loc[summer_months, 'mean'].mean()
            winter_avg = monthly_avg.loc[
                [m for m in monthly_avg.index if m not in summer_months], 'mean'
            ].mean()
            
            ac_usage_indicator = (summer_avg - winter_avg) / winter_avg * 100
            has_ac = ac_usage_indicator > 25
        else:
            has_ac = False
            ac_usage_indicator = 0
        
        return {
            'detected': True,
            'seasonality_level': seasonality,
            'variation_percentage': float(variation_pct),
            'peak_month': int(peak_month),
            'low_month': int(low_month),
            'likely_has_ac': has_ac,
            'ac_usage_indicator': float(ac_usage_indicator),
            'monthly_averages': monthly_avg['mean'].to_dict()
        }
    
    def cluster_users(
        self,
        user_features: pd.DataFrame,
        n_clusters: int = 5
    ) -> Tuple[np.ndarray, Dict]:
        """
        Cluster users based on consumption patterns
        
        Args:
            user_features: Aggregated features per user
            n_clusters: Number of clusters
            
        Returns:
            Cluster labels and cluster characteristics
        """
        # Scale features
        features_scaled = self.scaler.fit_transform(user_features)
        
        # Apply K-Means clustering
        self.kmeans_model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        cluster_labels = self.kmeans_model.fit_predict(features_scaled)
        
        # Analyze clusters
        cluster_characteristics = {}
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_data = user_features[cluster_mask]
            
            cluster_characteristics[cluster_id] = {
                'size': int(cluster_mask.sum()),
                'avg_consumption': float(cluster_data.mean().mean()),
                'avg_features': cluster_data.mean().to_dict(),
                'description': self._describe_cluster(cluster_data)
            }
        
        self.behavioral_clusters = cluster_characteristics
        
        return cluster_labels, cluster_characteristics
    
    def _describe_cluster(self, cluster_data: pd.DataFrame) -> str:
        """Generate human-readable cluster description"""
        avg_consumption = cluster_data.mean().mean()
        
        if avg_consumption > cluster_data.mean().mean() * 1.5:
            base = "High consumption"
        elif avg_consumption < cluster_data.mean().mean() * 0.7:
            base = "Low consumption"
        else:
            base = "Moderate consumption"
        
        # Add more characteristics based on available features
        return f"{base} user group"
    
    def learn_all_patterns(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Learn all lifestyle patterns from user data
        
        Args:
            data: Complete user usage data
            
        Returns:
            Dictionary of all detected patterns
        """
        logger.info("Learning lifestyle patterns...")
        
        patterns = {
            'sleep_cycle': self.detect_sleep_cycle(data),
            'work_hours': self.detect_work_hours(data),
            'weekend_pattern': self.detect_weekend_pattern(data),
            'seasonal_pattern': self.detect_seasonal_patterns(data),
            'learning_date': datetime.utcnow().isoformat(),
            'data_points': len(data)
        }
        
        self.patterns = patterns
        logger.info("Pattern learning complete")
        
        return patterns
    
    def get_pattern_summary(self) -> str:
        """Get human-readable summary of learned patterns"""
        if not self.patterns:
            return "No patterns learned yet"
        
        summary_parts = []
        
        # Sleep cycle
        if self.patterns['sleep_cycle']['detected']:
            sleep = self.patterns['sleep_cycle']
            summary_parts.append(
                f"Typical sleep: {sleep['sleep_start_hour']}:00 - {sleep['sleep_end_hour']}:00"
            )
        
        # Work hours
        if self.patterns['work_hours']['detected']:
            work = self.patterns['work_hours']
            if work['works_from_home']:
                summary_parts.append("Works from home")
            else:
                summary_parts.append(
                    f"Works outside: {work['work_start_hour']}:00 - {work['work_end_hour']}:00"
                )
        
        # Weekend
        if self.patterns['weekend_pattern']['detected']:
            weekend = self.patterns['weekend_pattern']
            summary_parts.append(f"Weekend pattern: {weekend['pattern_type']}")
        
        # Seasonal
        if self.patterns['seasonal_pattern']['detected']:
            seasonal = self.patterns['seasonal_pattern']
            summary_parts.append(
                f"Seasonality: {seasonal['seasonality_level']}"
            )
            if seasonal['likely_has_ac']:
                summary_parts.append("Likely has AC")
        
        return " | ".join(summary_parts)
    
    def save(self, path: str = None):
        """Save learned patterns and models"""
        path = path or self.model_path
        
        if self.kmeans_model:
            joblib.dump(self.kmeans_model, f"{path}/kmeans_model.pkl")
        joblib.dump(self.scaler, f"{path}/scaler.pkl")
        joblib.dump(self.patterns, f"{path}/patterns.pkl")
        
        logger.info(f"Pattern models saved to {path}")
    
    def load(self, path: str = None):
        """Load learned patterns and models"""
        path = path or self.model_path
        
        try:
            self.kmeans_model = joblib.load(f"{path}/kmeans_model.pkl")
            self.scaler = joblib.load(f"{path}/scaler.pkl")
            self.patterns = joblib.load(f"{path}/patterns.pkl")
            logger.info(f"Pattern models loaded from {path}")
        except FileNotFoundError:
            logger.warning(f"Pattern models not found at {path}")
