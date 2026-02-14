"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import secrets
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    # Project Information
    PROJECT_NAME: str = "AI-Powered Predictive Electricity Billing System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://localhost:8000",
    "http://127.0.0.1:5173",  
]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/electricity_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # External APIs
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    
    SMART_METER_API_KEY: Optional[str] = None
    SMART_METER_API_URL: str = "https://api.smartmeter.example.com"
    
    UTILITY_TARIFF_API_KEY: Optional[str] = None
    UTILITY_TARIFF_API_URL: str = "https://api.utility.example.com"
    
    # ML Configuration
    MODEL_PATH: str = "models/"
    MODEL_UPDATE_INTERVAL: int = 86400  # 24 hours in seconds
    PREDICTION_UPDATE_INTERVAL: int = 600  # 10 minutes
    PREDICTION_ERROR_THRESHOLD: float = 0.1  # 10%
    PATTERN_LEARNING_WINDOW_DAYS: int = 30
    MIN_DATA_POINTS_FOR_PREDICTION: int = 100
    
    # Alert Configuration
    ALERT_THRESHOLD_PERCENTAGE: float = 20.0  # Alert if bill exceeds 20% of expected
    ALERT_CHECK_INTERVAL: int = 3600  # Check every hour
    
    # Notification Services
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@electricitybilling.ai"
    
    SMS_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    PUSH_NOTIFICATION_ENABLED: bool = False
    FCM_SERVER_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Feature Flags
    ENABLE_WEATHER_INTEGRATION: bool = True
    ENABLE_APPLIANCE_DETECTION: bool = True
    ENABLE_RL_RECOMMENDATIONS: bool = True
    ENABLE_SOCIAL_COMPARISON: bool = False
    
    # Performance
    CACHE_ENABLED: bool = True
    ASYNC_PROCESSING: bool = True
    MAX_CONCURRENT_PREDICTIONS: int = 10
    
    # Data Retention
    USAGE_DATA_RETENTION_DAYS: int = 730  # 2 years
    PREDICTION_HISTORY_RETENTION_DAYS: int = 365  # 1 year
    ALERT_HISTORY_RETENTION_DAYS: int = 90  # 3 months
    
    # Tariff Configuration (Default Indian Tariff - can be customized)
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_TARIFF_SLABS: dict = {
        "0-100": 3.50,
        "101-200": 4.50,
        "201-400": 6.00,
        "401-500": 7.00,
        "500+": 8.00
    }
    FIXED_CHARGE: float = 50.0  # Monthly fixed charge
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
