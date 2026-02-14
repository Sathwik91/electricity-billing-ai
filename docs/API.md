# API Documentation
## AI-Powered Predictive Electricity Billing System

Base URL: `http://localhost:8000/api/v1`

---

## Authentication

### Register User
**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone_number": "+91-9876543210"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-02-01T10:00:00Z"
}
```

### Login
**POST** `/auth/login`

Authenticate and receive access token.

**Request Body (Form Data):**
```
username: user@example.com
password: SecurePass123!
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Refresh Token
**POST** `/auth/refresh`

Get new access token using refresh token.

---

## User Management

### Get Current User
**GET** `/users/me`

Get authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "+91-9876543210",
  "alert_threshold_percentage": 20.0,
  "timezone": "Asia/Kolkata",
  "profile": {
    "household_size": 4,
    "house_area_sqft": 1500,
    "house_type": "apartment",
    "location_city": "Bangalore",
    "appliances": [...]
  }
}
```

### Update Profile
**PUT** `/users/profile`

Update user profile information.

**Request Body:**
```json
{
  "household_size": 4,
  "house_area_sqft": 1500,
  "house_type": "apartment",
  "location_city": "Bangalore",
  "appliances": [
    {"name": "AC", "count": 2, "power_rating": 1500},
    {"name": "Refrigerator", "count": 1, "power_rating": 200}
  ],
  "ac_usage": "moderate"
}
```

---

## Usage Data

### Submit Usage Data
**POST** `/usage/`

Submit electricity consumption reading.

**Request Body:**
```json
{
  "timestamp": "2024-02-01T14:30:00Z",
  "consumption_kwh": 2.5,
  "temperature_celsius": 28.5,
  "humidity_percentage": 65.0,
  "appliance_breakdown": {
    "AC": 1.5,
    "Refrigerator": 0.3,
    "Others": 0.7
  }
}
```

**Response:** `201 Created`

### Get Current Usage
**GET** `/usage/current`

Get latest usage reading.

**Response:** `200 OK`
```json
{
  "timestamp": "2024-02-01T14:30:00Z",
  "consumption_kwh": 2.5,
  "temperature_celsius": 28.5,
  "hour_of_day": 14,
  "is_weekend": false
}
```

### Get Usage History
**GET** `/usage/history`

Get historical usage data.

**Query Parameters:**
- `days` (optional): Number of days (default: 30, max: 365)
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `aggregation` (optional): hourly|daily|monthly (default: daily)

**Example:** `/usage/history?days=7&aggregation=daily`

**Response:** `200 OK`
```json
[
  {
    "date": "2024-02-01",
    "total_consumption_kwh": 45.3,
    "avg_consumption_kwh": 1.89,
    "peak_consumption_kwh": 3.2,
    "avg_temperature": 28.5
  },
  ...
]
```

### Sync Smart Meter Data
**POST** `/usage/sync`

Sync data from smart meter API.

**Response:** `200 OK`
```json
{
  "synced_records": 120,
  "last_sync": "2024-02-01T14:30:00Z"
}
```

---

## Predictions

### Get Current Month Prediction
**GET** `/predictions/current-month`

Get real-time forecast for current billing month.

**Response:** `200 OK`
```json
{
  "predicted_consumption_kwh": 650.5,
  "current_consumption_kwh": 420.2,
  "predicted_remaining_kwh": 230.3,
  "predicted_bill_amount": 4250.0,
  "fixed_charge": 50.0,
  "confidence_score": 0.87,
  "days_remaining": 15,
  "percentage_change": 12.5,
  "tariff_breakdown": [
    {"slab": "0-100", "units": 100, "rate": 3.5, "amount": 350},
    {"slab": "101-200", "units": 100, "rate": 4.5, "amount": 450},
    ...
  ]
}
```

### Get Consumption Forecast
**GET** `/predictions/forecast`

Get daily consumption forecast.

**Query Parameters:**
- `days`: Number of days ahead (1-90)

**Example:** `/predictions/forecast?days=7`

**Response:** `200 OK`
```json
{
  "predictions": [15.2, 16.1, 14.8, 15.5, 16.3, 18.2, 17.5],
  "mean": 16.23,
  "total": 113.6,
  "confidence_interval": {
    "lower": [14.1, 14.9, ...],
    "upper": [16.3, 17.3, ...]
  }
}
```

### Recalculate Prediction
**POST** `/predictions/recalculate`

Force recalculation of current prediction.

**Response:** `200 OK`

### Get Prediction History
**GET** `/predictions/history`

Get historical predictions with actual values.

**Query Parameters:**
- `months`: Number of months (default: 6, max: 24)

**Response:** `200 OK`
```json
[
  {
    "billing_month": "2024-01",
    "predicted_consumption_kwh": 620.0,
    "actual_consumption_kwh": 615.3,
    "predicted_bill_amount": 4100.0,
    "actual_bill_amount": 4050.0,
    "prediction_error": 0.76,
    "accuracy_percentage": 99.24
  },
  ...
]
```

### Get Accuracy Metrics
**GET** `/predictions/accuracy`

Get overall prediction accuracy statistics.

**Response:** `200 OK`
```json
{
  "mae": 25.3,
  "rmse": 35.7,
  "mape": 4.2,
  "accuracy_percentage": 95.8,
  "total_predictions": 6,
  "accurate_predictions": 5
}
```

### Get Bill Comparison
**GET** `/predictions/comparison`

Compare current month with previous months.

**Response:** `200 OK`
```json
{
  "current_month": {
    "month": "2024-02",
    "projected_bill": 4250.0,
    "projected_consumption": 650.5
  },
  "previous_month": {
    "month": "2024-01",
    "bill": 4050.0,
    "consumption": 615.3
  },
  "difference": {
    "amount": 200.0,
    "percentage": 4.94
  },
  "trend": "increasing"
}
```

### Submit Actual Bill
**POST** `/predictions/actual`

Submit actual bill for accuracy tracking.

**Request Body:**
```json
{
  "month": "2024-01",
  "actual_consumption": 615.3,
  "actual_amount": 4050.0
}
```

---

## Recommendations

### Get Active Recommendations
**GET** `/recommendations/active`

Get personalized AI recommendations.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "type": "reduce_ac",
    "title": "Reduce AC Usage",
    "description": "Reduce AC usage by 1 hour daily",
    "estimated_savings_kwh": 1.5,
    "estimated_savings_amount": 420.0,
    "effort_level": "easy",
    "relevance_score": 0.92,
    "priority": 1,
    "action_steps": [
      "Set AC timer to turn off 1 hour earlier",
      "Use fans during cooler parts of the day"
    ]
  },
  ...
]
```

### Accept Recommendation
**POST** `/recommendations/{id}/accept`

Accept and commit to implementing a recommendation.

**Response:** `200 OK`

### Submit Feedback
**POST** `/recommendations/feedback`

Provide feedback on implemented recommendation.

**Request Body:**
```json
{
  "recommendation_id": 1,
  "implemented": true,
  "rating": 5,
  "feedback_text": "Great suggestion, saved significant amount!"
}
```

### Get Recommendation History
**GET** `/recommendations/history`

Get history of past recommendations and outcomes.

---

## Alerts

### Get Active Alerts
**GET** `/alerts/active`

Get all active alerts for the user.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "alert_type": "bill_threshold",
    "status": "active",
    "title": "Bill Threshold Exceeded",
    "message": "At current usage, your bill is projected to reach ₹4,500. This is 20% higher than expected.",
    "severity": "warning",
    "current_projected_bill": 4500.0,
    "threshold_bill": 3750.0,
    "excess_amount": 750.0,
    "potential_savings": 420.0,
    "suggested_actions": [
      {
        "action": "Reduce AC usage by 1 hour daily",
        "savings": 420.0
      }
    ],
    "created_at": "2024-02-01T10:00:00Z"
  }
]
```

### Acknowledge Alert
**PUT** `/alerts/{id}/acknowledge`

Mark alert as acknowledged.

**Response:** `200 OK`

### Update Alert Settings
**POST** `/alerts/settings`

Update user's alert preferences.

**Request Body:**
```json
{
  "alert_threshold_percentage": 15.0,
  "enable_email_alerts": true,
  "enable_sms_alerts": false,
  "enable_push_alerts": true,
  "quiet_hours": {
    "start": "22:00",
    "end": "08:00"
  }
}
```

---

## Lifestyle Patterns

### Get Learned Patterns
**GET** `/patterns/`

Get all learned lifestyle patterns.

**Response:** `200 OK`
```json
{
  "sleep_cycle": {
    "detected": true,
    "sleep_start_hour": 23,
    "sleep_end_hour": 7,
    "sleep_duration_hours": 8,
    "confidence": 0.89
  },
  "work_hours": {
    "detected": true,
    "works_from_home": false,
    "work_start_hour": 9,
    "work_end_hour": 18,
    "confidence": 0.85
  },
  "weekend_pattern": {
    "detected": true,
    "weekend_avg_consumption": 18.5,
    "weekday_avg_consumption": 14.2,
    "difference_percentage": 30.3,
    "pattern_type": "high_weekend_usage"
  },
  "seasonal_pattern": {
    "detected": true,
    "seasonality_level": "high",
    "peak_month": 5,
    "low_month": 11,
    "likely_has_ac": true
  }
}
```

### Refresh Patterns
**POST** `/patterns/refresh`

Trigger pattern relearning from latest data.

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "error": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "error": "NOT_FOUND",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

- **Default**: 60 requests per minute per user
- **Burst**: 1000 requests per hour per user

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1612345678
```

---

## Webhooks

Configure webhooks to receive real-time notifications.

### Available Events
- `prediction.updated` - New prediction calculated
- `alert.created` - New alert generated
- `bill.threshold_exceeded` - Bill threshold exceeded
- `recommendation.generated` - New recommendation available

### Webhook Payload
```json
{
  "event": "alert.created",
  "timestamp": "2024-02-01T10:00:00Z",
  "data": {
    "alert_id": 1,
    "user_id": 123,
    "alert_type": "bill_threshold",
    ...
  }
}
```

---

## SDK Examples

### Python
```python
import requests

API_URL = "http://localhost:8000/api/v1"
token = "your_access_token"

headers = {"Authorization": f"Bearer {token}"}

# Get current prediction
response = requests.get(f"{API_URL}/predictions/current-month", headers=headers)
prediction = response.json()
print(f"Predicted bill: ₹{prediction['predicted_bill_amount']}")
```

### JavaScript
```javascript
const API_URL = 'http://localhost:8000/api/v1';
const token = 'your_access_token';

const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Get recommendations
fetch(`${API_URL}/recommendations/active`, { headers })
  .then(res => res.json())
  .then(data => console.log('Recommendations:', data));
```

### cURL
```bash
# Get current month prediction
curl -X GET "http://localhost:8000/api/v1/predictions/current-month" \
  -H "Authorization: Bearer your_access_token"
```

---

## Support

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Email**: support@electricitybilling.ai
- **GitHub**: https://github.com/yourorg/electricity-billing-ai
