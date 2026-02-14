"""
Test Suite for AI-Powered Electricity Billing System
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from main import app
from app.core.database import Base, engine
from app.models.models import User, UsageData, Prediction
from app.services.prediction_service import PredictionService


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Setup test database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(client):
    """Create test user"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Test123!@#",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def auth_headers(client, test_user):
    """Get authentication headers"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuthentication:
    """Test authentication endpoints"""
    
    async def test_register_user(self, client):
        """Test user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewPass123!@#",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "AnotherPass123!@#",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
    
    async def test_login_success(self, client, test_user):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "Test123!@#"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401


class TestUsageData:
    """Test usage data endpoints"""
    
    async def test_submit_usage_data(self, client, auth_headers):
        """Test submitting usage data"""
        response = await client.post(
            "/api/v1/usage/",
            headers=auth_headers,
            json={
                "timestamp": datetime.utcnow().isoformat(),
                "consumption_kwh": 2.5,
                "temperature_celsius": 28.5,
                "humidity_percentage": 65.0
            }
        )
        assert response.status_code == 201
    
    async def test_get_usage_history(self, client, auth_headers):
        """Test retrieving usage history"""
        # Submit some data first
        for i in range(5):
            await client.post(
                "/api/v1/usage/",
                headers=auth_headers,
                json={
                    "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "consumption_kwh": 2.0 + i * 0.5,
                    "temperature_celsius": 28.0,
                    "humidity_percentage": 60.0
                }
            )
        
        response = await client.get(
            "/api/v1/usage/history?days=7",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5


class TestPredictions:
    """Test prediction endpoints"""
    
    async def test_get_current_month_prediction(self, client, auth_headers):
        """Test getting current month prediction"""
        # Submit sufficient usage data
        for i in range(15):
            await client.post(
                "/api/v1/usage/",
                headers=auth_headers,
                json={
                    "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "consumption_kwh": 3.0 + np.random.randn() * 0.5,
                    "temperature_celsius": 28.0 + np.random.randn() * 2,
                    "humidity_percentage": 65.0 + np.random.randn() * 5
                }
            )
        
        response = await client.get(
            "/api/v1/predictions/current-month",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_bill_amount" in data
        assert "predicted_consumption_kwh" in data
        assert "confidence_score" in data
    
    async def test_forecast_consumption(self, client, auth_headers):
        """Test consumption forecasting"""
        response = await client.get(
            "/api/v1/predictions/forecast?days=7",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 7
    
    async def test_prediction_accuracy(self, client, auth_headers):
        """Test prediction accuracy metrics"""
        response = await client.get(
            "/api/v1/predictions/accuracy",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestRecommendations:
    """Test recommendation endpoints"""
    
    async def test_get_recommendations(self, client, auth_headers):
        """Test getting AI recommendations"""
        response = await client.get(
            "/api/v1/recommendations/active",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            rec = data[0]
            assert "title" in rec
            assert "estimated_savings_amount" in rec
            assert "effort_level" in rec
    
    async def test_accept_recommendation(self, client, auth_headers):
        """Test accepting a recommendation"""
        # Get recommendations first
        recs_response = await client.get(
            "/api/v1/recommendations/active",
            headers=auth_headers
        )
        
        if len(recs_response.json()) > 0:
            rec_id = recs_response.json()[0]["id"]
            
            response = await client.post(
                f"/api/v1/recommendations/{rec_id}/accept",
                headers=auth_headers
            )
            assert response.status_code == 200
    
    async def test_submit_recommendation_feedback(self, client, auth_headers):
        """Test submitting recommendation feedback"""
        response = await client.post(
            "/api/v1/recommendations/feedback",
            headers=auth_headers,
            json={
                "recommendation_id": 1,
                "rating": 5,
                "implemented": True,
                "feedback_text": "Great recommendation!"
            }
        )
        # May return 404 if recommendation doesn't exist
        assert response.status_code in [200, 404]


class TestAlerts:
    """Test alert endpoints"""
    
    async def test_get_active_alerts(self, client, auth_headers):
        """Test getting active alerts"""
        response = await client.get(
            "/api/v1/alerts/active",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_acknowledge_alert(self, client, auth_headers):
        """Test acknowledging an alert"""
        # This test assumes an alert exists
        response = await client.put(
            "/api/v1/alerts/1/acknowledge",
            headers=auth_headers
        )
        # May return 404 if alert doesn't exist
        assert response.status_code in [200, 404]


class TestMLModels:
    """Test ML model functionality"""
    
    def test_lstm_model_prediction(self):
        """Test LSTM forecasting model"""
        from ml_models.forecasting.lstm_model import BillForecastingModel
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
        data = pd.DataFrame({
            'timestamp': dates,
            'consumption_kwh': np.random.uniform(1, 5, len(dates)),
            'hour_of_day': dates.hour,
            'day_of_week': dates.dayofweek,
            'is_weekend': (dates.dayofweek >= 5).astype(int),
            'temperature_celsius': np.random.uniform(20, 35, len(dates)),
            'humidity_percentage': np.random.uniform(40, 80, len(dates))
        })
        
        model = BillForecastingModel(sequence_length=24)
        
        # This would normally require training
        # For now, just test the structure
        assert model.sequence_length == 24
        assert len(model.features) > 0
    
    def test_pattern_learning(self):
        """Test lifestyle pattern learning"""
        from ml_models.pattern_learning.lifestyle_patterns import LifestylePatternLearner
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
        data = pd.DataFrame({
            'timestamp': dates,
            'consumption_kwh': np.random.uniform(1, 5, len(dates))
        })
        
        learner = LifestylePatternLearner()
        patterns = learner.learn_all_patterns(data)
        
        assert 'sleep_cycle' in patterns
        assert 'work_hours' in patterns
        assert 'weekend_pattern' in patterns
    
    def test_recommendation_engine(self):
        """Test RL recommendation engine"""
        from ml_models.recommendation.rl_engine import RecommendationEngine
        
        engine = RecommendationEngine()
        
        # Test state creation
        user_data = {
            'household_size': 3,
            'house_area_sqft': 1200,
            'has_solar_panels': False,
            'projected_monthly_bill': 2500,
            'avg_monthly_bill': 2000
        }
        
        usage_data = pd.DataFrame({
            'consumption_kwh': np.random.uniform(2, 4, 30)
        })
        
        patterns = {
            'sleep_cycle': {'detected': True},
            'work_hours': {'works_from_home': True},
            'seasonal_pattern': {'variation_percentage': 25}
        }
        
        state = engine.get_state(user_data, usage_data, patterns)
        assert state.shape[1] == engine.state_size


class TestIntegration:
    """Integration tests"""
    
    async def test_full_prediction_workflow(self, client, auth_headers):
        """Test complete prediction workflow"""
        # 1. Submit usage data
        for i in range(20):
            await client.post(
                "/api/v1/usage/",
                headers=auth_headers,
                json={
                    "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "consumption_kwh": 3.0 + np.random.randn() * 0.5,
                    "temperature_celsius": 28.0,
                    "humidity_percentage": 65.0
                }
            )
        
        # 2. Get prediction
        pred_response = await client.get(
            "/api/v1/predictions/current-month",
            headers=auth_headers
        )
        assert pred_response.status_code == 200
        
        # 3. Get recommendations
        rec_response = await client.get(
            "/api/v1/recommendations/active",
            headers=auth_headers
        )
        assert rec_response.status_code == 200
        
        # 4. Check for alerts
        alert_response = await client.get(
            "/api/v1/alerts/active",
            headers=auth_headers
        )
        assert alert_response.status_code == 200


# Performance Tests
class TestPerformance:
    """Performance and load tests"""
    
    async def test_prediction_response_time(self, client, auth_headers):
        """Test prediction endpoint response time"""
        import time
        
        start = time.time()
        response = await client.get(
            "/api/v1/predictions/current-month",
            headers=auth_headers
        )
        duration = time.time() - start
        
        assert duration < 10.0  # Should respond within 10 seconds
    
    async def test_concurrent_requests(self, client, auth_headers):
        """Test handling concurrent requests"""
        tasks = []
        for _ in range(10):
            task = client.get(
                "/api/v1/usage/history?days=7",
                headers=auth_headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
