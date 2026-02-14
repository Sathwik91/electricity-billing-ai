# AI-Powered Predictive Electricity Billing System

## Overview
A production-ready AI-based system that forecasts monthly electricity bills in real-time by learning lifestyle and appliance usage patterns, providing personalized cost-saving recommendations.

## Features
- **Real-time Monitoring**: Track electricity consumption as it happens
- **Lifestyle Pattern Learning**: AI detects sleep cycles, work hours, weekend behavior, and seasonal patterns
- **Predictive Billing**: Accurate monthly bill forecasting (±10% error after learning phase)
- **Smart Alerts**: Notifications when projected bills exceed thresholds
- **AI Recommendations**: Personalized energy-saving suggestions using Reinforcement Learning
- **Interactive Dashboard**: Mobile-friendly UI with real-time insights

## Architecture

### Tech Stack
- **Backend**: Python 3.11, FastAPI, Celery
- **ML/AI**: TensorFlow, scikit-learn, Prophet
- **Database**: PostgreSQL 15, Redis
- **Frontend**: React 18, TypeScript, TailwindCSS
- **Infrastructure**: Docker, Kubernetes, Prometheus, Grafana

### System Components
1. **Data Acquisition Layer**: Smart meter integration, IoT device connectors
2. **ML Pipeline**: Pattern learning, forecasting, recommendation engines
3. **API Layer**: RESTful APIs with authentication
4. **Notification Service**: Alert system with multi-channel support
5. **User Interface**: Responsive web dashboard

## Project Structure
```
electricity-billing-ai/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Config, security, dependencies
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── ml-models/              # Machine learning components
│   ├── pattern_learning/   # Lifestyle pattern detection
│   ├── forecasting/        # Bill prediction models
│   ├── recommendation/     # RL-based recommendations
│   └── training/           # Model training scripts
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   └── package.json
├── infrastructure/         # DevOps configuration
│   ├── docker/            # Dockerfiles
│   ├── kubernetes/        # K8s manifests
│   └── monitoring/        # Prometheus, Grafana configs
├── database/              # Database schemas and scripts
├── tests/                 # Test suites
└── docs/                  # Documentation

```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd electricity-billing-ai
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configurations
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Initialize the database**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Train initial ML models**
```bash
docker-compose exec ml-service python train_models.py
```

6. **Access the application**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Monitoring: http://localhost:9090

## Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/electricity_db
REDIS_URL=redis://localhost:6379

# API Keys
WEATHER_API_KEY=your_weather_api_key
SMART_METER_API_KEY=your_smart_meter_key
UTILITY_TARIFF_API_KEY=your_tariff_key

# ML Configuration
MODEL_UPDATE_INTERVAL=86400  # 24 hours
PREDICTION_THRESHOLD=0.1     # 10% error margin

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Alerts
ALERT_THRESHOLD_PERCENTAGE=20
EMAIL_SERVICE_URL=smtp.gmail.com
```

## API Documentation

### Authentication
```bash
POST /api/v1/auth/login
POST /api/v1/auth/register
```

### Usage Data
```bash
GET  /api/v1/usage/current
GET  /api/v1/usage/history?start_date=2024-01-01&end_date=2024-01-31
POST /api/v1/usage/sync
```

### Predictions
```bash
GET  /api/v1/predictions/current-month
GET  /api/v1/predictions/forecast?days=7
POST /api/v1/predictions/recalculate
```

### Recommendations
```bash
GET  /api/v1/recommendations/active
POST /api/v1/recommendations/feedback
GET  /api/v1/recommendations/history
```

### Alerts
```bash
GET  /api/v1/alerts/active
PUT  /api/v1/alerts/{alert_id}/acknowledge
POST /api/v1/alerts/settings
```

## ML Models

### 1. Lifestyle Pattern Learning
- **Algorithm**: K-Means Clustering + Time-Series Analysis
- **Features**: Hour-of-day, day-of-week, consumption patterns
- **Update Frequency**: Daily
- **Accuracy Target**: 85% pattern recognition

### 2. Bill Forecasting
- **Algorithm**: LSTM + Prophet (Hybrid)
- **Features**: Historical usage, weather, patterns, tariffs
- **Update Frequency**: Every 10 minutes
- **Accuracy Target**: ±10% prediction error

### 3. Recommendation Engine
- **Algorithm**: Deep Q-Network (DQN) with contextual bandits
- **Actions**: 20+ energy-saving recommendations
- **Reward**: Cost savings + user satisfaction
- **Update Frequency**: Based on user feedback

## Testing

### Run all tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Integration tests
cd tests
pytest integration/ -v

# Load tests
locust -f tests/load_tests.py
```

### Test Coverage
- Unit Tests: >80% coverage
- Integration Tests: Critical paths
- End-to-End Tests: User journeys
- Load Tests: 1000 concurrent users

## Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to Kubernetes
kubectl apply -f infrastructure/kubernetes/

# Monitor deployment
kubectl get pods -n electricity-billing
```

### Scaling
- Horizontal Pod Autoscaling configured for API and ML services
- Database read replicas for high availability
- Redis cluster for distributed caching

## Monitoring & Logging

### Metrics
- Request latency (p50, p95, p99)
- Model prediction accuracy
- Alert response times
- System resource utilization

### Logging
- Centralized logging with ELK stack
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request/response logging with correlation IDs

### Alerting
- Prometheus alerts for system health
- PagerDuty integration for critical issues
- Slack notifications for warnings

## Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting

### Data Protection
- End-to-end encryption for sensitive data
- Data anonymization for ML training
- GDPR compliance

### Security Best Practices
- Regular security audits
- Dependency vulnerability scanning
- Secrets management with Vault

## Performance Optimization

### Backend
- Response caching with Redis
- Database query optimization
- Async processing with Celery

### Frontend
- Code splitting and lazy loading
- Image optimization
- Service Worker for offline support

### ML Models
- Model quantization for faster inference
- Batch prediction for efficiency
- Model versioning and A/B testing

## Contributing

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- GitHub Issues: [Project Issues](https://github.com/yourorg/electricity-billing-ai/issues)
- Documentation: [Full Docs](docs/)
- Email: support@yourcompany.com

## Roadmap

### Phase 1 (Current)
- ✅ Core prediction engine
- ✅ Basic pattern learning
- ✅ REST API
- ✅ Web dashboard

### Phase 2
- 🔄 Mobile app (iOS/Android)
- 🔄 Advanced RL recommendations
- 🔄 Multi-language support
- 🔄 Utility provider integration

### Phase 3
- ⏳ Solar panel integration
- ⏳ Community benchmarking
- ⏳ Predictive maintenance
- ⏳ Energy trading marketplace

## Acknowledgments

- TensorFlow team for ML framework
- FastAPI for the excellent web framework
- React community for frontend tools
