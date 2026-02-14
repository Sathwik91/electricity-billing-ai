"""
Prometheus Metrics for Monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# API Metrics
# ============================================================================

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# Active requests
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# ============================================================================
# User Metrics
# ============================================================================

# Total users
total_users = Gauge(
    'total_users',
    'Total number of registered users'
)

# Active users (logged in last 24h)
active_users = Gauge(
    'active_users_24h',
    'Number of users active in last 24 hours'
)

# User logins
user_logins_total = Counter(
    'user_logins_total',
    'Total number of user logins',
    ['status']  # success, failed
)

# ============================================================================
# Electricity Usage Metrics
# ============================================================================

# Current consumption by user
current_consumption_kwh = Gauge(
    'current_consumption_kwh',
    'Current electricity consumption in kWh',
    ['user_id']
)

# Daily consumption
daily_consumption_kwh = Gauge(
    'daily_consumption_kwh',
    'Daily electricity consumption in kWh',
    ['user_id', 'date']
)

# Monthly bill predictions
predicted_bill_amount = Gauge(
    'predicted_bill_amount',
    'Predicted monthly bill amount',
    ['user_id', 'currency']
)

# Total consumption across all users
total_consumption_kwh = Gauge(
    'total_consumption_kwh',
    'Total electricity consumption across all users'
)

# ============================================================================
# ML Model Metrics
# ============================================================================

# LSTM predictions
lstm_predictions_total = Counter(
    'lstm_predictions_total',
    'Total number of LSTM predictions made',
    ['user_id', 'status']  # success, failed
)

# LSTM prediction duration
lstm_prediction_duration_seconds = Histogram(
    'lstm_prediction_duration_seconds',
    'LSTM prediction duration in seconds',
    ['user_id'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Pattern learning executions
pattern_learning_total = Counter(
    'pattern_learning_total',
    'Total pattern learning executions',
    ['user_id', 'pattern_type']
)

# RL recommendations
rl_recommendations_total = Counter(
    'rl_recommendations_total',
    'Total RL recommendations generated',
    ['user_id']
)

# RL feedback
rl_feedback_total = Counter(
    'rl_feedback_total',
    'Total RL feedback received',
    ['user_id', 'accepted', 'implemented']
)

# Model accuracy
model_accuracy = Gauge(
    'model_accuracy_percentage',
    'ML model accuracy percentage',
    ['user_id', 'model_type']  # lstm, rl
)

# ============================================================================
# Database Metrics
# ============================================================================

# Database queries
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']  # select, insert, update, delete
)

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# Database connection pool
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_total = Gauge(
    'db_connections_total',
    'Total database connections in pool'
)

# ============================================================================
# Recommendation Metrics
# ============================================================================

# Recommendations generated
recommendations_generated_total = Counter(
    'recommendations_generated_total',
    'Total recommendations generated',
    ['user_id', 'type']
)

# Recommendation acceptance rate
recommendation_acceptance_rate = Gauge(
    'recommendation_acceptance_rate',
    'Recommendation acceptance rate percentage',
    ['user_id']
)

# Estimated savings from recommendations
estimated_savings_kwh = Gauge(
    'estimated_savings_kwh',
    'Estimated energy savings from recommendations',
    ['user_id']
)

# ============================================================================
# System Metrics
# ============================================================================

# App info
app_info = Info(
    'app_info',
    'Application information'
)

# Celery tasks
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks executed',
    ['task_name', 'status']
)

# Celery task duration
celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)

# ============================================================================
# Alert Metrics
# ============================================================================

# Alerts triggered
alerts_triggered_total = Counter(
    'alerts_triggered_total',
    'Total alerts triggered',
    ['user_id', 'alert_type', 'severity']
)

# ============================================================================
# Helper Functions
# ============================================================================

def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_lstm_prediction(user_id: int, duration: float, success: bool):
    """Track LSTM prediction metrics"""
    status = "success" if success else "failed"
    lstm_predictions_total.labels(user_id=user_id, status=status).inc()
    if success:
        lstm_prediction_duration_seconds.labels(user_id=user_id).observe(duration)


def track_rl_feedback(user_id: int, accepted: bool, implemented: bool):
    """Track RL feedback"""
    rl_feedback_total.labels(
        user_id=user_id,
        accepted=str(accepted),
        implemented=str(implemented)
    ).inc()


def track_db_query(operation: str, duration: float):
    """Track database query"""
    db_queries_total.labels(operation=operation).inc()
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def set_app_info(version: str, environment: str):
    """Set application information"""
    app_info.info({
        'version': version,
        'environment': environment,
        'name': 'AI-Powered Electricity Billing System'
    })


# Decorator for tracking function execution time
def track_time(metric: Histogram, labels: dict = None):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator