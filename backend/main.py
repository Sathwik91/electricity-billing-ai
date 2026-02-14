"""
Main FastAPI application with Prometheus Monitoring
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from sqlalchemy import select
import calendar
import random
from app.integrations.factory import ProviderFactory
from app.models.models import User, UsageData
from app.core.database import async_session_maker

from app.core.config import settings
from app.api.v1 import api_router
from app.core.exceptions import AppException
from app.services.ml_service import MLService
from app.utils.logger import setup_logging
from app.core.metrics import (
    set_app_info,
    track_request_metrics,
    http_requests_in_progress,
    total_users,
    active_users,
    current_consumption_kwh,
    total_consumption_kwh,
    predicted_bill_amount,
    recommendation_acceptance_rate,
    estimated_savings_kwh
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def update_metrics_task():
    """Background task to update metrics every 30 seconds"""
    logger.info("🔄 Metrics updater background task started")
    
    # Wait for database to be ready
    await asyncio.sleep(5)
    
    while True:
        try:
            logger.info("📊 Updating metrics from database...")
            
            from app.models.models import User, UsageData, Recommendation
            from app.core.database import async_session_maker
            
            def calculate_bill(consumption_kwh: float) -> float:
                FIXED_CHARGE = 50
                bill = FIXED_CHARGE
                remaining = consumption_kwh
                slabs = [
                    (0, 100, 3.50), (101, 200, 4.50), (201, 400, 6.00),
                    (401, 500, 7.00), (501, float('inf'), 8.00)
                ]
                for lower, upper, rate in slabs:
                    if remaining <= 0:
                        break
                    units = min(remaining, upper - lower + 1) if upper != float('inf') else remaining
                    bill += units * rate
                    remaining -= units
                return bill
            
            async with async_session_maker() as session:
                # Get users
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                user_count = len(users)
                logger.info(f"   Found {user_count} users")
                
                if user_count == 0:
                    logger.warning("   ⚠️  No users found in database!")
                    await asyncio.sleep(30)
                    continue
                
                total_users.set(user_count)
                active_users.set(user_count)
                
                total_consumption_all = 0
                
                for user in users:
                    # Get usage data
                    result = await session.execute(
                        select(UsageData)
                        .filter(UsageData.user_id == user.id)
                        .order_by(UsageData.timestamp.desc())
                        .limit(1000)
                    )
                    usage_records = result.scalars().all()
                    
                    logger.info(f"   User {user.id}: {len(usage_records)} usage records")
                    
                    if not usage_records:
                        current_consumption_kwh.labels(user_id=str(user.id)).set(0)
                        predicted_bill_amount.labels(user_id=str(user.id), currency="INR").set(50)
                        continue
                    
                    # Today's consumption
                    today = datetime.utcnow().date()
                    today_consumption = sum(
                        r.consumption_kwh for r in usage_records 
                        if r.timestamp.date() == today
                    )
                    
                    if today_consumption == 0:
                        yesterday = today - timedelta(days=1)
                        today_consumption = sum(
                            r.consumption_kwh for r in usage_records 
                            if r.timestamp.date() == yesterday
                        )
                    
                    if today_consumption == 0 and usage_records:
                        # Use average from recent data
                        recent = usage_records[:48]
                        today_consumption = sum(r.consumption_kwh for r in recent) / 2
                    
                    logger.info(f"   User {user.id} consumption: {today_consumption:.2f} kWh")
                    
                    current_consumption_kwh.labels(user_id=str(user.id)).set(today_consumption)
                    total_consumption_all += today_consumption
                    
                    # Predicted bill
                    now = datetime.utcnow()
                    month_start = datetime(now.year, now.month, 1)
                    month_consumption = sum(
                        r.consumption_kwh for r in usage_records 
                        if r.timestamp >= month_start
                    )
                    
                    days_in_month = calendar.monthrange(now.year, now.month)[1]
                    days_elapsed = now.day
                    days_remaining = days_in_month - days_elapsed
                    
                    if days_elapsed > 0:
                        daily_avg = month_consumption / days_elapsed
                        predicted_remaining = daily_avg * days_remaining
                    else:
                        predicted_remaining = 0
                    
                    total_predicted = month_consumption + predicted_remaining
                    predicted_bill = calculate_bill(total_predicted)
                    predicted_bill_amount.labels(user_id=str(user.id), currency="INR").set(predicted_bill)
                    
                    # Recommendations
                    result = await session.execute(
                        select(Recommendation).filter(Recommendation.user_id == user.id)
                    )
                    recommendations = result.scalars().all()
                    
                    if recommendations:
                        accepted = sum(1 for r in recommendations if r.status in ['accepted', 'implemented'])
                        rate = (accepted / len(recommendations)) * 100
                        recommendation_acceptance_rate.labels(user_id=str(user.id)).set(rate)
                        
                        total_savings = sum(r.estimated_savings_kwh or 0 for r in recommendations if r.status == 'implemented')
                        estimated_savings_kwh.labels(user_id=str(user.id)).set(total_savings)
                
                total_consumption_kwh.set(total_consumption_all)
                
                logger.info(f"✅ Metrics updated: {user_count} users, {total_consumption_all:.2f} kWh total")
        
        except Exception as e:
            logger.error(f"❌ Error updating metrics: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(30)

from app.integrations.factory import ProviderFactory

async def generate_daily_usage():
    """Background task to generate usage data every hour"""
    print("📊 Daily usage generator started")
    
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            print(f"⏰ Generating usage data for {datetime.now().strftime('%Y-%m-%d %H:00')}")
            
            # Get weather data from provider
            weather_provider = ProviderFactory.get_weather_provider()
            latitude = float(os.getenv("DEFAULT_LATITUDE", "12.9716"))
            longitude = float(os.getenv("DEFAULT_LONGITUDE", "77.5946"))
            
            try:
                weather = await weather_provider.get_current_weather(latitude, longitude)
                temperature = weather.temperature_celsius
                humidity = weather.humidity_percentage
            except Exception as e:
                print(f"  ⚠️  Could not fetch weather, using defaults: {e}")
                temperature = random.uniform(20, 35)
                humidity = random.uniform(40, 80)
            
            async with async_session_maker() as db:
                # Get all users
                result = await db.execute(select(User))
                users = result.scalars().all()
                
                current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
                
                for user in users:
                    # Try to get real smart meter data
                    smart_meter_provider = ProviderFactory.get_smart_meter_provider()
                    
                    try:
                        # Assume meter_id is stored in user table or use user.id
                        meter_id = f"METER_{user.id}"
                        reading = await smart_meter_provider.get_current_reading(meter_id)
                        consumption = reading.consumption_kwh
                        
                        print(f"  📡 Got real reading for {user.email}: {consumption:.2f} kWh")
                        
                    except Exception as e:
                        # If real data fails, generate simulated
                        hour = current_time.hour
                        base = random.uniform(0.5, 2.0)
                        
                        if 0 <= hour < 6:
                            multiplier = random.uniform(0.3, 0.5)
                        elif 6 <= hour < 9:
                            multiplier = random.uniform(1.0, 1.5)
                        elif 9 <= hour < 17:
                            multiplier = random.uniform(0.6, 1.0)
                        elif 17 <= hour < 22:
                            multiplier = random.uniform(1.2, 1.8)
                        else:
                            multiplier = random.uniform(0.4, 0.6)
                        
                        # Weather impact
                        if temperature > 30:
                            multiplier *= 1.2  # AC usage
                        
                        is_weekend = current_time.weekday() >= 5
                        if is_weekend:
                            multiplier *= 1.2
                        
                        consumption = base * multiplier
                    
                    # Check if record exists
                    existing = await db.execute(
                        select(UsageData).where(
                            UsageData.user_id == user.id,
                            UsageData.timestamp == current_time
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        print(f"  ⏭️  Skipping {user.email} - data exists")
                        continue
                    
                    # Create usage record
                    usage_record = UsageData(
                        user_id=user.id,
                        timestamp=current_time,
                        consumption_kwh=consumption,
                        hour_of_day=current_time.hour,
                        day_of_week=current_time.weekday(),
                        is_weekend=is_weekend,
                        temperature_celsius=temperature,
                        humidity_percentage=humidity
                    )
                    
                    db.add(usage_record)
                    print(f"  ✅ Generated {consumption:.2f} kWh for {user.email}")
                
                await db.commit()
                print(f"✅ Usage data generation complete\n")
                
        except Exception as e:
            print(f"❌ Error in usage generation: {e}")
            import traceback
            traceback.print_exc()
 
async def cleanup_old_data():
    """Remove data older than 90 days"""
    while True:
        try:
            await asyncio.sleep(86400)  # Run once per day
            
            cutoff_date = datetime.now() - timedelta(days=90)
            
            async with async_session_maker() as db:
                result = await db.execute(
                    delete(UsageData).where(UsageData.timestamp < cutoff_date)
                )
                await db.commit()
                
                print(f"🗑️ Cleaned up {result.rowcount} old usage records")
                
        except Exception as e:
            print(f"Error in cleanup: {e}")

# Add to lifespan:
cleanup_task = asyncio.create_task(cleanup_old_data())

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events"""
    print("🚀 Starting up...")
    print("="*50)

     # Initialize data providers FIRST
    await ProviderFactory.initialize()
    
    # Start background tasks
    print("📊 Starting metrics updater...")
    metrics_task = asyncio.create_task(update_metrics_task())
    
    print("⚡ Starting usage data generator...")
    usage_task = asyncio.create_task(generate_daily_usage())
    
    print("✅ All background tasks started")
    print("="*50)
    
    yield
    
    print("\n🛑 Shutting down...")
    print("="*50)
    
    # Cancel background tasks
    print("Cancelling metrics updater...")
    metrics_task.cancel()
    
    print("Cancelling usage generator...")
    usage_task.cancel()
    
    try:
        await metrics_task
        await usage_task
    except asyncio.CancelledError:
        print("✅ Background tasks cancelled successfully")
    
    print("="*50)
    print("👋 Shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-based Predictive Electricity Billing System with Real-time Monitoring",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    method = request.method

    http_requests_in_progress.labels(
        method=method,
        endpoint=endpoint
    ).inc()

    start_time = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start_time

        track_request_metrics(
            method,
            endpoint,
            response.status_code,
            duration
        )

        response.headers["X-Process-Time"] = f"{duration:.4f}"

        if duration > 1.0:
            logger.warning(
                f"Slow request: {method} {endpoint} took {duration:.2f}s"
            )

        return response
    finally:
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
        }
    )


# Health endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health/ready")
async def readiness_check():
    ml_service = app.state.ml_service
    if not ml_service.check_models_loaded():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"}
        )
    return {"status": "ready"}


# Test endpoint to manually trigger metrics update
@app.post("/admin/update-metrics")
async def manual_update_metrics():
    """Manual endpoint to trigger metrics update"""
    try:
        from app.models.models import User
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            total_users.set(len(users))
            active_users.set(len(users))
            
            logger.info(f"✅ Manual metrics update: {len(users)} users")
            
            return {
                "status": "success",
                "users": len(users),
                "message": "Metrics updated successfully"
            }
    except Exception as e:
        logger.error(f"Error updating metrics: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


# Prometheus endpoint
Instrumentator(
    should_ignore_untemplated=True
).instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False
)


@app.get("/")
async def root():
    return {
        "message": "AI-Powered Predictive Electricity Billing System",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )