"""
Advanced LSTM model with attention mechanism
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Tuple, List
import joblib


class AttentionLayer(layers.Layer):
    """Attention mechanism for LSTM"""
    
    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)
    
    def build(self, input_shape):
        self.W = self.add_weight(
            name='attention_weight',
            shape=(input_shape[-1], input_shape[-1]),
            initializer='glorot_uniform',
            trainable=True
        )
        self.b = self.add_weight(
            name='attention_bias',
            shape=(input_shape[-1],),
            initializer='zeros',
            trainable=True
        )
        super(AttentionLayer, self).build(input_shape)
    
    def call(self, inputs):
        # inputs shape: (batch_size, time_steps, features)
        score = tf.nn.tanh(tf.tensordot(inputs, self.W, axes=1) + self.b)
        attention_weights = tf.nn.softmax(score, axis=1)
        context_vector = attention_weights * inputs
        context_vector = tf.reduce_sum(context_vector, axis=1)
        return context_vector


def create_advanced_lstm_model(
    sequence_length: int,
    n_features: int,
    dropout_rate: float = 0.3
) -> keras.Model:
    """
    Create advanced LSTM with attention and residual connections
    """
    inputs = keras.Input(shape=(sequence_length, n_features))
    
    # First LSTM layer with return sequences
    lstm1 = layers.LSTM(128, return_sequences=True, dropout=dropout_rate)(inputs)
    lstm1 = layers.BatchNormalization()(lstm1)
    
    # Second LSTM layer
    lstm2 = layers.LSTM(64, return_sequences=True, dropout=dropout_rate)(lstm1)
    lstm2 = layers.BatchNormalization()(lstm2)
    
    # Attention mechanism
    attention = AttentionLayer()(lstm2)
    
    # Dense layers with residual connection
    dense1 = layers.Dense(64, activation='relu')(attention)
    dense1 = layers.Dropout(dropout_rate)(dense1)
    dense1 = layers.BatchNormalization()(dense1)
    
    dense2 = layers.Dense(32, activation='relu')(dense1)
    dense2 = layers.Dropout(dropout_rate)(dense2)
    
    # Output layer
    outputs = layers.Dense(1, activation='linear')(dense2)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    
    # Use custom optimizer with learning rate schedule
    lr_schedule = keras.optimizers.schedules.ExponentialDecay(
        initial_learning_rate=0.001,
        decay_steps=1000,
        decay_rate=0.9
    )
    
    optimizer = keras.optimizers.Adam(learning_rate=lr_schedule)
    
    model.compile(
        optimizer=optimizer,
        loss='huber',  # More robust than MSE
        metrics=['mae', 'mse']
    )
    
    return model


def create_ensemble_models(
    sequence_length: int,
    n_features: int,
    n_models: int = 3
) -> List[keras.Model]:
    """Create ensemble of models for better predictions"""
    models = []
    
    for i in range(n_models):
        # Vary architecture slightly for diversity
        model = create_advanced_lstm_model(
            sequence_length=sequence_length,
            n_features=n_features,
            dropout_rate=0.2 + (i * 0.1)  # Different dropout rates
        )
        models.append(model)
    
    return models


class AdvancedLSTMPredictor:
    """Advanced predictor with ensemble and uncertainty estimation"""
    
    def __init__(self, sequence_length: int = 168):
        self.sequence_length = sequence_length
        self.models = []
        self.scaler_X = None
        self.scaler_y = None
        self.feature_names = None
    
    def prepare_sequences(
        self, 
        X: np.ndarray, 
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM"""
        X_seq = []
        y_seq = []
        
        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:i + self.sequence_length])
            y_seq.append(y[i + self.sequence_length])
        
        return np.array(X_seq), np.array(y_seq)
    
    def train(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32
    ):
        """Train ensemble of models"""
        # Prepare sequences
        X_seq, y_seq = self.prepare_sequences(X, y)
        
        print(f"Training on {len(X_seq)} sequences")
        print(f"Sequence shape: {X_seq.shape}")
        
        # Create ensemble
        n_features = X_seq.shape[2]
        self.models = create_ensemble_models(
            sequence_length=self.sequence_length,
            n_features=n_features,
            n_models=3
        )
        
        # Early stopping and model checkpoint
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        # Train each model
        for i, model in enumerate(self.models):
            print(f"\nTraining model {i+1}/{len(self.models)}...")
            
            history = model.fit(
                X_seq, y_seq,
                validation_split=validation_split,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )
            
            print(f"Model {i+1} - Final val_loss: {history.history['val_loss'][-1]:.4f}")
    
    def predict(self, X: np.ndarray) -> Tuple[float, float, float]:
        """
        Predict with uncertainty estimation
        Returns: (mean_prediction, std_prediction, confidence)
        """
        X_seq, _ = self.prepare_sequences(X, np.zeros(len(X)))
        
        if len(X_seq) == 0:
            return 0.0, 0.0, 0.0
        
        # Get predictions from all models
        predictions = []
        for model in self.models:
            pred = model.predict(X_seq[-1:], verbose=0)
            predictions.append(pred[0][0])
        
        predictions = np.array(predictions)
        
        # Calculate statistics
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        
        # Calculate confidence (inverse of coefficient of variation)
        if mean_pred != 0:
            cv = std_pred / abs(mean_pred)
            confidence = 1 / (1 + cv)  # High confidence when low variation
        else:
            confidence = 0.5
        
        # Clip confidence between 0.7 and 0.99
        confidence = np.clip(confidence, 0.70, 0.99)
        
        return float(mean_pred), float(std_pred), float(confidence)
    
    def save(self, filepath: str):
        """Save all models"""
        for i, model in enumerate(self.models):
            model.save(f"{filepath}_model_{i}.h5")
        
        # Save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'n_models': len(self.models)
        }
        joblib.dump(metadata, f"{filepath}_metadata.pkl")
    
    def load(self, filepath: str):
        """Load all models"""
        metadata = joblib.dump(f"{filepath}_metadata.pkl")
        
        self.sequence_length = metadata['sequence_length']
        self.models = []
        
        for i in range(metadata['n_models']):
            model = keras.models.load_model(
                f"{filepath}_model_{i}.h5",
                custom_objects={'AttentionLayer': AttentionLayer}
            )
            self.models.append(model)