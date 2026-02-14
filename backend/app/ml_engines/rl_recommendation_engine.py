"""
Reinforcement Learning Recommendation Engine using Deep Q-Network (DQN)
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from collections import deque
import random
import json
import os


class RecommendationAction:
    """Available recommendation actions"""
    
    ACTIONS = [
        {
            'id': 'reduce_ac_temp',
            'title': 'Reduce AC Temperature',
            'description': 'Increase AC temperature by 2°C to reduce energy consumption',
            'base_savings': 1.5,  # kWh per day
            'effort': 'easy',
            'category': 'cooling'
        },
        {
            'id': 'led_upgrade',
            'title': 'Switch to LED Bulbs',
            'description': 'Replace remaining incandescent bulbs with LED alternatives',
            'base_savings': 2.0,
            'effort': 'moderate',
            'category': 'lighting'
        },
        {
            'id': 'standby_power',
            'title': 'Eliminate Standby Power',
            'description': 'Use smart plugs to eliminate vampire power drain',
            'base_savings': 0.6,
            'effort': 'easy',
            'category': 'devices'
        },
        {
            'id': 'optimize_fridge',
            'title': 'Optimize Refrigerator',
            'description': 'Clean coils, check seals, and set optimal temperature (3-5°C)',
            'base_savings': 0.8,
            'effort': 'easy',
            'category': 'appliances'
        },
        {
            'id': 'water_heater_timer',
            'title': 'Install Water Heater Timer',
            'description': 'Use timer to heat water only when needed',
            'base_savings': 1.2,
            'effort': 'moderate',
            'category': 'heating'
        },
        {
            'id': 'smart_thermostat',
            'title': 'Install Smart Thermostat',
            'description': 'Automatically optimize heating/cooling schedules',
            'base_savings': 2.5,
            'effort': 'hard',
            'category': 'automation'
        },
        {
            'id': 'shift_heavy_loads',
            'title': 'Shift Heavy Load Usage',
            'description': 'Run washing machine, dryer during off-peak hours',
            'base_savings': 0.5,
            'effort': 'easy',
            'category': 'scheduling'
        },
        {
            'id': 'insulation_upgrade',
            'title': 'Improve Insulation',
            'description': 'Add weather stripping, seal gaps to reduce heating/cooling loss',
            'base_savings': 1.8,
            'effort': 'hard',
            'category': 'building'
        },
        {
            'id': 'fan_instead_ac',
            'title': 'Use Fans Instead of AC',
            'description': 'Use ceiling/standing fans when temperature is moderate',
            'base_savings': 2.2,
            'effort': 'easy',
            'category': 'cooling'
        },
        {
            'id': 'solar_investment',
            'title': 'Consider Solar Panels',
            'description': 'Invest in rooftop solar for long-term savings',
            'base_savings': 5.0,
            'effort': 'hard',
            'category': 'generation'
        }
    ]
    
    @classmethod
    def get_action(cls, action_id):
        """Get action by ID"""
        for action in cls.ACTIONS:
            if action['id'] == action_id:
                return action
        return None
    
    @classmethod
    def get_all_actions(cls):
        """Get all available actions"""
        return cls.ACTIONS


class RLRecommendationEngine:
    """Deep Q-Network for personalized recommendations"""
    
    def __init__(self, state_size=15, action_size=10):
        self.state_size = state_size
        self.action_size = action_size
        
        # Hyperparameters
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # Experience replay
        self.memory = deque(maxlen=2000)
        self.batch_size = 32
        
        # Build models
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
    def _build_model(self):
        """Build neural network for Q-learning"""
        model = keras.Sequential([
            keras.layers.Dense(128, input_dim=self.state_size, activation='relu'),
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
        """Copy weights from model to target_model"""
        self.target_model.set_weights(self.model.get_weights())
    
    def get_state(self, user_data, usage_data, patterns):
        """
        Create state vector from user data
        
        State features (15 dimensions):
        1. Average daily consumption (normalized)
        2. Current month consumption trend
        3. Has AC (0/1)
        4. House size (normalized)
        5. Number of occupants (normalized)
        6. Hour of day (normalized)
        7. Is weekend (0/1)
        8. Temperature (normalized)
        9. Sleep cycle regularity (0-1)
        10. Work from home (0/1)
        11. Weekend usage spike (0-1)
        12. Seasonal variation (0-1)
        13. Bill vs target (ratio)
        14. Days into month (normalized)
        15. Previous recommendation acceptance rate (0-1)
        """
        state = np.zeros(self.state_size)
        
        # Normalize values
        state[0] = min(user_data.get('avg_daily_consumption', 0) / 50.0, 1.0)
        state[1] = min(user_data.get('consumption_trend', 0) / 100.0, 1.0)
        state[2] = 1.0 if user_data.get('has_ac', False) else 0.0
        state[3] = min(user_data.get('house_size', 100) / 300.0, 1.0)
        state[4] = min(user_data.get('occupants', 1) / 6.0, 1.0)
        state[5] = usage_data.get('hour', 12) / 24.0
        state[6] = 1.0 if usage_data.get('is_weekend', False) else 0.0
        state[7] = min(usage_data.get('temperature', 25) / 45.0, 1.0)
        state[8] = patterns.get('sleep_regularity', 0.5)
        state[9] = 1.0 if patterns.get('works_from_home', False) else 0.0
        state[10] = min(patterns.get('weekend_spike', 0) / 2.0, 1.0)
        state[11] = patterns.get('seasonality', 0.5)
        state[12] = min(user_data.get('bill_ratio', 1.0), 2.0) / 2.0
        state[13] = min(user_data.get('days_into_month', 15) / 31.0, 1.0)
        state[14] = user_data.get('acceptance_rate', 0.5)
        
        return state
    
    def get_recommendations(self, state, top_k=3):
        """Get top K recommendations for given state"""
        if np.random.rand() <= self.epsilon:
            # Exploration: random recommendations
            action_indices = random.sample(range(self.action_size), min(top_k, self.action_size))
        else:
            # Exploitation: use learned Q-values
            q_values = self.model.predict(state.reshape(1, -1), verbose=0)[0]
            action_indices = np.argsort(q_values)[-top_k:][::-1]
        
        recommendations = []
        for idx in action_indices:
            if idx < len(RecommendationAction.ACTIONS):
                action = RecommendationAction.ACTIONS[idx]
                recommendations.append({
                    'action_id': action['id'],
                    'action_index': int(idx),
                    'title': action['title'],
                    'description': action['description'],
                    'estimated_savings_kwh': action['base_savings'],
                    'effort_level': action['effort'],
                    'category': action['category']
                })
        
        return recommendations
    
    def remember(self, state, action_idx, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action_idx, reward, next_state, done))
    
    def replay(self):
        """Train on batch of experiences"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample random batch
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.array([exp[0] for exp in minibatch])
        actions = np.array([exp[1] for exp in minibatch])
        rewards = np.array([exp[2] for exp in minibatch])
        next_states = np.array([exp[3] for exp in minibatch])
        dones = np.array([exp[4] for exp in minibatch])
        
        # Current Q values
        current_q = self.model.predict(states, verbose=0)
        
        # Next Q values from target model
        next_q = self.target_model.predict(next_states, verbose=0)
        
        # Update Q values
        for i in range(self.batch_size):
            if dones[i]:
                current_q[i][actions[i]] = rewards[i]
            else:
                current_q[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])
        
        # Train
        self.model.fit(states, current_q, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def calculate_reward(self, feedback):
        """
        Calculate reward based on user feedback
        
        Feedback structure:
        {
            'accepted': bool,
            'implemented': bool,
            'rating': int (1-5),
            'actual_savings': float (kWh),
            'estimated_savings': float (kWh),
            'time_to_implement': int (days)
        }
        """
        reward = 0.0
        
        # Base rewards
        if feedback.get('accepted', False):
            reward += 5.0
        else:
            reward -= 2.0
        
        if feedback.get('implemented', False):
            reward += 10.0
            
            # Bonus for actual savings
            actual = feedback.get('actual_savings', 0)
            estimated = feedback.get('estimated_savings', 1)
            
            if actual > 0:
                # Reward based on accuracy
                accuracy = min(actual / estimated, 2.0)
                reward += accuracy * 5.0
                
                # Extra reward for high savings
                if actual >= estimated:
                    reward += 5.0
            
            # Penalty for slow implementation
            days = feedback.get('time_to_implement', 7)
            if days > 30:
                reward -= 2.0
        
        # Rating bonus
        rating = feedback.get('rating', 3)
        reward += (rating - 3) * 2.0  # -4 to +4
        
        return reward
    
    def save(self, path):
        """Save model and parameters"""
        os.makedirs(path, exist_ok=True)
        
        # Save models
        self.model.save(f"{path}/rl_model.h5")
        self.target_model.save(f"{path}/rl_target_model.h5")
        
        # Save parameters
        params = {
            'epsilon': self.epsilon,
            'state_size': self.state_size,
            'action_size': self.action_size,
            'gamma': self.gamma,
            'learning_rate': self.learning_rate
        }
        
        with open(f"{path}/rl_params.json", 'w') as f:
            json.dump(params, f)
        
        print(f"✅ RL model saved to {path}")
    
    def load(self, path):
        """Load model and parameters"""
        try:
            # Load models
            self.model = keras.models.load_model(f"{path}/rl_model.h5")
            self.target_model = keras.models.load_model(f"{path}/rl_target_model.h5")
            
            # Load parameters
            with open(f"{path}/rl_params.json", 'r') as f:
                params = json.load(f)
            
            self.epsilon = params.get('epsilon', self.epsilon)
            
            print(f"✅ RL model loaded from {path}")
            return True
        except Exception as e:
            print(f"❌ RL load error: {str(e)}")
            return False


# Utility function to initialize RL engine
def create_rl_engine():
    """Create and return RL engine"""
    return RLRecommendationEngine(state_size=15, action_size=10)