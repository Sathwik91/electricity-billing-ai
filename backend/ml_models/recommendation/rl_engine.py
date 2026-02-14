"""
Reinforcement Learning Recommendation Engine
Uses Deep Q-Network (DQN) to learn optimal energy-saving recommendations
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import deque
import random
import tensorflow as tf
from tensorflow import keras
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    RL-based recommendation engine for personalized energy-saving suggestions
    """
    
    # Define action space (recommendations)
    ACTIONS = [
        {
            'id': 0,
            'type': 'reduce_ac',
            'title': 'Reduce AC Usage',
            'description': 'Reduce AC usage by 1 hour daily',
            'avg_savings_kwh': 1.5,
            'effort': 'easy'
        },
        {
            'id': 1,
            'type': 'adjust_temperature',
            'title': 'Adjust AC Temperature',
            'description': 'Set AC to 24°C instead of 22°C',
            'avg_savings_kwh': 0.8,
            'effort': 'easy'
        },
        {
            'id': 2,
            'type': 'shift_washing',
            'title': 'Shift Washing Machine Usage',
            'description': 'Run washing machine during off-peak hours',
            'avg_savings_kwh': 0.5,
            'effort': 'moderate'
        },
        {
            'id': 3,
            'type': 'led_upgrade',
            'title': 'Upgrade to LED Bulbs',
            'description': 'Replace remaining incandescent bulbs with LEDs',
            'avg_savings_kwh': 2.0,
            'effort': 'moderate'
        },
        {
            'id': 4,
            'type': 'geyser_timer',
            'title': 'Use Geyser Timer',
            'description': 'Set water heater on timer (1 hour before use)',
            'avg_savings_kwh': 1.2,
            'effort': 'easy'
        },
        {
            'id': 5,
            'type': 'fan_over_ac',
            'title': 'Use Fans When Possible',
            'description': 'Use ceiling fans instead of AC when weather permits',
            'avg_savings_kwh': 2.5,
            'effort': 'moderate'
        },
        {
            'id': 6,
            'type': 'appliance_maintenance',
            'title': 'Maintain Appliances',
            'description': 'Clean AC filters and refrigerator coils',
            'avg_savings_kwh': 1.0,
            'effort': 'moderate'
        },
        {
            'id': 7,
            'type': 'standby_power',
            'title': 'Eliminate Standby Power',
            'description': 'Unplug devices or use smart power strips',
            'avg_savings_kwh': 0.6,
            'effort': 'easy'
        },
        {
            'id': 8,
            'type': 'natural_light',
            'title': 'Maximize Natural Light',
            'description': 'Use natural light during daytime',
            'avg_savings_kwh': 0.4,
            'effort': 'easy'
        },
        {
            'id': 9,
            'type': 'efficient_cooking',
            'title': 'Efficient Cooking',
            'description': 'Use pressure cooker and cover pots while cooking',
            'avg_savings_kwh': 0.7,
            'effort': 'easy'
        }
    ]
    
    def __init__(
        self,
        state_size: int = 15,
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        model_path: str = "models/recommendation/"
    ):
        self.state_size = state_size
        self.action_size = len(self.ACTIONS)
        self.learning_rate = learning_rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.model_path = model_path
        
        # Experience replay
        self.memory = deque(maxlen=2000)
        self.batch_size = 32
        
        # Build DQN model
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
    def _build_model(self) -> keras.Model:
        """Build Deep Q-Network"""
        model = keras.Sequential([
            keras.layers.Dense(128, activation='relu', input_dim=self.state_size),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(self.action_size, activation='linear')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        
        return model
    
    def update_target_model(self):
        """Update target model weights"""
        self.target_model.set_weights(self.model.get_weights())
    
    def get_state(
        self,
        user_data: Dict,
        usage_data: pd.DataFrame,
        patterns: Dict
    ) -> np.ndarray:
        """
        Create state representation from user context
        
        Args:
            user_data: User profile information
            usage_data: Recent usage data
            patterns: Learned lifestyle patterns
            
        Returns:
            State vector
        """
        state = []
        
        # Usage statistics (normalized)
        avg_daily_kwh = usage_data['consumption_kwh'].mean()
        max_daily_kwh = usage_data['consumption_kwh'].max()
        std_daily_kwh = usage_data['consumption_kwh'].std()
        
        state.extend([
            avg_daily_kwh / 50,  # Normalize to typical range
            max_daily_kwh / 100,
            std_daily_kwh / 20
        ])
        
        # Time-based features
        current_hour = pd.Timestamp.now().hour
        current_day = pd.Timestamp.now().dayofweek
        state.extend([
            current_hour / 24,
            current_day / 7,
            1 if current_day >= 5 else 0  # Is weekend
        ])
        
        # User profile features
        state.extend([
            user_data.get('household_size', 2) / 6,
            user_data.get('house_area_sqft', 1000) / 3000,
            1 if user_data.get('has_solar_panels', False) else 0
        ])
        
        # Pattern features
        state.extend([
            1 if patterns.get('sleep_cycle', {}).get('detected', False) else 0,
            1 if patterns.get('work_hours', {}).get('works_from_home', False) else 0,
            patterns.get('seasonal_pattern', {}).get('variation_percentage', 0) / 100
        ])
        
        # Current bill trajectory
        projected_bill = user_data.get('projected_monthly_bill', 2000)
        avg_bill = user_data.get('avg_monthly_bill', 2000)
        state.extend([
            projected_bill / 5000,
            (projected_bill - avg_bill) / avg_bill if avg_bill > 0 else 0,
            1 if projected_bill > avg_bill * 1.2 else 0  # Bill alert threshold
        ])
        
        return np.array(state).reshape(1, -1)
    
    def select_action(self, state: np.ndarray, explore: bool = True) -> int:
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current state
            explore: Whether to explore (training) or exploit (inference)
            
        Returns:
            Action index
        """
        if explore and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])
    
    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """Train on batch from replay memory"""
        if len(self.memory) < self.batch_size:
            return
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.array([experience[0][0] for experience in minibatch])
        actions = np.array([experience[1] for experience in minibatch])
        rewards = np.array([experience[2] for experience in minibatch])
        next_states = np.array([experience[3][0] for experience in minibatch])
        dones = np.array([experience[4] for experience in minibatch])
        
        # Predict Q-values
        current_q_values = self.model.predict(states, verbose=0)
        next_q_values = self.target_model.predict(next_states, verbose=0)
        
        # Update Q-values with rewards
        for i in range(self.batch_size):
            if dones[i]:
                current_q_values[i][actions[i]] = rewards[i]
            else:
                current_q_values[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
        
        # Train model
        self.model.fit(states, current_q_values, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def calculate_reward(
        self,
        action_id: int,
        user_feedback: Optional[Dict] = None,
        actual_savings: Optional[float] = None
    ) -> float:
        """
        Calculate reward for taken action
        
        Args:
            action_id: Action that was taken
            user_feedback: User's response to recommendation
            actual_savings: Actual savings achieved (if available)
            
        Returns:
            Reward value
        """
        action = self.ACTIONS[action_id]
        base_reward = 0
        
        if user_feedback:
            # User accepted recommendation
            if user_feedback.get('accepted', False):
                base_reward += 5
                
                # User implemented recommendation
                if user_feedback.get('implemented', False):
                    base_reward += 10
                    
                    # Positive user rating
                    rating = user_feedback.get('rating', 0)
                    base_reward += rating * 2
                    
                    # Actual savings achieved
                    if actual_savings:
                        expected_savings = action['avg_savings_kwh']
                        if actual_savings >= expected_savings * 0.8:
                            base_reward += 15
                        else:
                            base_reward += 5
            else:
                # User rejected recommendation
                base_reward -= 2
        
        # Effort penalty (harder recommendations need better rewards)
        effort_penalty = {
            'easy': 0,
            'moderate': -1,
            'difficult': -2
        }
        base_reward += effort_penalty.get(action['effort'], 0)
        
        return base_reward
    
    def get_recommendations(
        self,
        user_data: Dict,
        usage_data: pd.DataFrame,
        patterns: Dict,
        n_recommendations: int = 3
    ) -> List[Dict]:
        """
        Get top N personalized recommendations
        
        Args:
            user_data: User profile
            usage_data: Recent usage data
            patterns: Learned patterns
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        state = self.get_state(user_data, usage_data, patterns)
        q_values = self.model.predict(state, verbose=0)[0]
        
        # Get top actions
        top_action_indices = np.argsort(q_values)[-n_recommendations:][::-1]
        
        recommendations = []
        for idx in top_action_indices:
            action = self.ACTIONS[idx].copy()
            
            # Personalize savings estimate
            avg_daily_kwh = usage_data['consumption_kwh'].mean()
            personalized_savings = self._personalize_savings(
                action['avg_savings_kwh'],
                avg_daily_kwh,
                user_data,
                patterns
            )
            
            # Calculate monetary savings (assuming ₹6/kWh average)
            avg_rate = 6.0
            monthly_savings_amount = personalized_savings * 30 * avg_rate
            
            recommendations.append({
                'id': idx,
                'type': action['type'],
                'title': action['title'],
                'description': action['description'],
                'estimated_savings_kwh': round(personalized_savings, 2),
                'estimated_savings_amount': round(monthly_savings_amount, 2),
                'effort_level': action['effort'],
                'relevance_score': float(q_values[idx]),
                'action_steps': self._get_action_steps(action['type']),
                'priority': len(top_action_indices) - list(top_action_indices).index(idx)
            })
        
        return recommendations
    
    def _personalize_savings(
        self,
        base_savings: float,
        avg_daily_kwh: float,
        user_data: Dict,
        patterns: Dict
    ) -> float:
        """Personalize savings estimate based on user context"""
        multiplier = 1.0
        
        # Adjust based on current consumption level
        if avg_daily_kwh > 30:
            multiplier *= 1.2
        elif avg_daily_kwh < 10:
            multiplier *= 0.8
        
        # Adjust based on household size
        household_size = user_data.get('household_size', 2)
        if household_size > 4:
            multiplier *= 1.1
        
        # Adjust based on AC usage patterns
        if patterns.get('seasonal_pattern', {}).get('likely_has_ac', False):
            multiplier *= 1.15
        
        return base_savings * multiplier
    
    def _get_action_steps(self, action_type: str) -> List[str]:
        """Get implementation steps for each action type"""
        steps_map = {
            'reduce_ac': [
                'Set AC timer to turn off 1 hour earlier',
                'Use fans during cooler parts of the day',
                'Monitor your comfort level and adjust gradually'
            ],
            'adjust_temperature': [
                'Gradually increase AC temperature by 1°C',
                'Ensure proper insulation to maintain comfort',
                'Clean AC filters for better efficiency'
            ],
            'shift_washing': [
                'Run washing machine after 10 PM or before 6 AM',
                'Batch laundry to maximize efficiency',
                'Use cold water when possible'
            ],
            'led_upgrade': [
                'Identify remaining non-LED bulbs',
                'Purchase equivalent LED replacements',
                'Replace bulbs in most-used rooms first'
            ],
            'geyser_timer': [
                'Install a digital timer on your geyser',
                'Set it to heat water 1 hour before typical usage',
                'Turn off manually when not needed'
            ],
            'fan_over_ac': [
                'Use fans when temperature is below 30°C',
                'Combine fan with AC at higher temperature',
                'Open windows during cooler evening hours'
            ],
            'appliance_maintenance': [
                'Clean AC filters monthly',
                'Vacuum refrigerator coils quarterly',
                'Check door seals on refrigerator and freezer'
            ],
            'standby_power': [
                'Use smart power strips for entertainment systems',
                'Unplug chargers when not in use',
                'Turn off computers instead of sleep mode'
            ],
            'natural_light': [
                'Open curtains during daytime',
                'Rearrange furniture to maximize natural light use',
                'Turn off lights in unoccupied rooms'
            ],
            'efficient_cooking': [
                'Use pressure cooker for faster cooking',
                'Keep lids on pots and pans',
                'Match pot size to burner size'
            ]
        }
        
        return steps_map.get(action_type, ['Implement this recommendation to save energy'])
    
    def save(self, path: str = None):
        """Save model"""
        path = path or self.model_path
        self.model.save(f"{path}/dqn_model.h5")
        self.target_model.save(f"{path}/dqn_target_model.h5")
        logger.info(f"Recommendation model saved to {path}")
    
    def load(self, path: str = None):
        """Load model"""
        path = path or self.model_path
        self.model = keras.models.load_model(f"{path}/dqn_model.h5")
        self.target_model = keras.models.load_model(f"{path}/dqn_target_model.h5")
        logger.info(f"Recommendation model loaded from {path}")
