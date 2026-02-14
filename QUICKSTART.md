# Quick Start Guide
## Get Running in 5 Minutes

This guide will get you up and running with the AI-Powered Predictive Electricity Billing System quickly.

---

## Prerequisites

Ensure you have installed:
- Docker Desktop (includes Docker Compose)
- Git

That's it! Everything else runs in containers.

---

## Step 1: Get the Code

```bash
# Clone repository
git clone https://github.com/yourorg/electricity-billing-ai.git
cd electricity-billing-ai
```

---

## Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# (Optional) Edit with your API keys
# For quick start, the defaults work fine
nano .env
```

**Minimum required changes:**
- Set a secure `SECRET_KEY` (or leave the default for testing)

---

## Step 3: Start Everything

```bash
# Start all services
docker-compose up -d

# This will:
# - Start PostgreSQL database
# - Start Redis cache
# - Start FastAPI backend
# - Start React frontend
# - Start Celery workers
# - Start monitoring tools
```

Wait 1-2 minutes for all services to start.

---

## Step 4: Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# The database is now initialized with demo users
```

---

## Step 5: Generate Demo Data

```bash
# Create sample users with realistic usage data
docker-compose exec backend python scripts/generate_demo_data.py

# This creates 5 demo users with 60 days of electricity usage data
```

---

## Step 6: Access the Application

Open your browser to:

- **Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

### Login Credentials

Use any of these demo accounts:

```
Email: demo1@example.com
Password: Demo123!@#

Email: demo2@example.com
Password: Demo123!@#

Email: demo3@example.com
Password: Demo123!@#
```

---

## What You'll See

### Dashboard Features

1. **Current Month Prediction**
   - Real-time bill forecast
   - Confidence score
   - Comparison with previous months

2. **Usage Charts**
   - Daily consumption trends
   - Hourly usage patterns
   - Peak usage times

3. **AI Recommendations**
   - Personalized energy-saving tips
   - Estimated savings
   - Easy-to-follow action steps

4. **Alerts**
   - Bill threshold warnings
   - Unusual usage notifications
   - Cost-saving opportunities

---

## Test the API

### Get Current Prediction

```bash
# First, login to get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo1@example.com&password=Demo123!@#" \
  | jq -r '.access_token')

# Get current month prediction
curl -X GET "http://localhost:8000/api/v1/predictions/current-month" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Submit New Usage Data

```bash
curl -X POST "http://localhost:8000/api/v1/usage/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-02-03T14:00:00Z",
    "consumption_kwh": 2.5,
    "temperature_celsius": 28.5,
    "humidity_percentage": 65.0
  }'
```

### Get Recommendations

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/active" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Explore the Features

### 1. Submit Daily Usage

Navigate to the dashboard and watch predictions update in real-time as you add usage data.

### 2. View Pattern Learning

Check the "Patterns" tab to see what the AI has learned about your lifestyle:
- Sleep cycle
- Work hours
- Weekend vs weekday usage
- Seasonal patterns

### 3. Get Personalized Recommendations

The RL engine provides tailored suggestions based on:
- Your usage patterns
- Your household profile
- Current consumption trends
- Weather conditions

### 4. Set Up Alerts

Configure custom thresholds for notifications when:
- Projected bill exceeds budget
- Unusual usage detected
- Better rates available

---

## Monitoring

Access these URLs to monitor the system:

- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3001 (admin/admin)
- **Celery Tasks**: http://localhost:5555

---

## Add Your Own Data

### Manual Entry

Use the dashboard to manually enter your electricity readings.

### Smart Meter Integration

Configure your smart meter API in `.env`:

```bash
SMART_METER_API_KEY=your_api_key_here
SMART_METER_API_URL=https://api.yourmeter.com
```

Then sync data:

```bash
curl -X POST "http://localhost:8000/api/v1/usage/sync" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Customize Tariffs

Update electricity tariff rates:

```bash
# Edit tariff in database
docker-compose exec postgres psql -U postgres electricity_db

# Update tariff_rates table
UPDATE tariff_rates 
SET rate_slabs = '{"0-100": 3.50, "101-200": 4.50, "201-400": 6.00, "401-500": 7.00, "500+": 8.00}'
WHERE utility_provider = 'Default Utility';
```

Or use the API:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/tariffs" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rate_slabs": {
      "0-100": 3.50,
      "101-200": 4.50,
      "201-400": 6.00
    },
    "fixed_charge": 50.0
  }'
```

---

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Everything

```bash
docker-compose down
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

---

## Next Steps

1. **Read the Full Documentation**
   - [API Documentation](docs/API.md)
   - [Deployment Guide](docs/DEPLOYMENT.md)
   - [Architecture Overview](docs/ARCHITECTURE.md)

2. **Customize for Your Needs**
   - Modify ML models
   - Add new recommendation types
   - Integrate with your utility provider

3. **Deploy to Production**
   - Follow the deployment guide
   - Set up SSL/TLS
   - Configure monitoring
   - Set up automated backups

---

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs

# Restart
docker-compose down
docker-compose up -d
```

### Database connection errors

```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready -U postgres
```

### Frontend not loading

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs frontend
```

### No predictions available

Predictions require at least 100 data points (about 4 days of hourly data).

```bash
# Generate more demo data
docker-compose exec backend python scripts/generate_demo_data.py
```

---

## Get Help

- **Documentation**: `docs/`
- **API Reference**: http://localhost:8000/docs
- **GitHub Issues**: https://github.com/yourorg/electricity-billing-ai/issues
- **Email**: support@electricitybilling.ai

---

## What's Next?

Now that you're running, explore:

1. The interactive API documentation at http://localhost:8000/docs
2. The monitoring dashboards at http://localhost:3001
3. The pattern learning in the "Insights" tab
4. The recommendation engine's suggestions

Enjoy your AI-powered electricity billing system! 🚀⚡
