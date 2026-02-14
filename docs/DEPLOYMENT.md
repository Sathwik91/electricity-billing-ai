# Deployment Guide
## AI-Powered Predictive Electricity Billing System

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker** 20.10+ and Docker Compose 2.0+
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+
- **Redis** 7+
- **Git**

### Optional but Recommended
- **kubectl** (for Kubernetes deployment)
- **helm** (for Kubernetes package management)
- **terraform** (for infrastructure as code)

---

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourorg/electricity-billing-ai.git
cd electricity-billing-ai
```

### 2. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Configuration:**
- Update `SECRET_KEY` with a random secure string
- Add your API keys (Weather, Smart Meter, etc.)
- Configure email/SMS settings if needed

### 3. Start Services with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify database
docker-compose exec postgres psql -U postgres -d electricity_db -c "\dt"
```

### 5. Train Initial ML Models
```bash
# Run model training
docker-compose exec ml-trainer python training/train_all_models.py

# Verify models
docker-compose exec backend ls -la models/
```

### 6. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:9090 (Prometheus)
- **Dashboards**: http://localhost:3001 (Grafana)
- **Celery Monitoring**: http://localhost:5555 (Flower)

### 7. Default Credentials
- **Admin**: admin@electricitybilling.ai / Admin123!@#
- **Demo User**: demo@electricitybilling.ai / Demo123!@#

---

## Production Deployment

### Option 1: Docker Compose Production

1. **Update Environment**
```bash
cp .env.example .env.production
# Edit with production settings
```

2. **Use Production Compose File**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **SSL/TLS Configuration**
```bash
# Generate SSL certificates
mkdir -p infrastructure/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infrastructure/nginx/ssl/nginx.key \
  -out infrastructure/nginx/ssl/nginx.crt

# Or use Let's Encrypt with certbot
docker-compose -f docker-compose.certbot.yml up
```

### Option 2: Kubernetes Deployment

1. **Prerequisites**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

2. **Create Kubernetes Secrets**
```bash
kubectl create namespace electricity-billing

kubectl create secret generic app-secrets \
  --from-env-file=.env.production \
  -n electricity-billing

kubectl create secret generic db-secrets \
  --from-literal=password=YOUR_DB_PASSWORD \
  -n electricity-billing
```

3. **Deploy to Kubernetes**
```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n electricity-billing
kubectl get services -n electricity-billing

# View logs
kubectl logs -f deployment/electricity-backend -n electricity-billing
```

4. **Configure Ingress**
```bash
# Install nginx ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx

# Apply ingress configuration
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

---

## Cloud Deployment

### AWS Deployment

1. **Infrastructure Setup with Terraform**
```bash
cd infrastructure/terraform/aws

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply configuration
terraform apply
```

2. **EKS Cluster Setup**
```bash
# Configure kubectl for EKS
aws eks update-kubeconfig --name electricity-billing-cluster --region us-east-1

# Deploy application
kubectl apply -f infrastructure/kubernetes/
```

3. **Configure RDS (PostgreSQL)**
```bash
# Create RDS instance via Terraform
terraform apply -target=module.rds

# Update DATABASE_URL in secrets
kubectl edit secret app-secrets -n electricity-billing
```

4. **Configure ElastiCache (Redis)**
```bash
# Create ElastiCache cluster
terraform apply -target=module.elasticache

# Update REDIS_URL in secrets
kubectl edit secret app-secrets -n electricity-billing
```

### Google Cloud Platform (GCP)

1. **GKE Setup**
```bash
# Create GKE cluster
gcloud container clusters create electricity-billing \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --zone=us-central1-a

# Get credentials
gcloud container clusters get-credentials electricity-billing
```

2. **Cloud SQL (PostgreSQL)**
```bash
# Create Cloud SQL instance
gcloud sql instances create electricity-db \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-2 \
  --region=us-central1

# Create database
gcloud sql databases create electricity_db --instance=electricity-db
```

3. **Deploy Application**
```bash
kubectl apply -f infrastructure/kubernetes/
```

### Azure Deployment

1. **AKS Setup**
```bash
# Create resource group
az group create --name electricity-billing-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group electricity-billing-rg \
  --name electricity-billing-aks \
  --node-count 3 \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group electricity-billing-rg --name electricity-billing-aks
```

2. **Azure Database for PostgreSQL**
```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group electricity-billing-rg \
  --name electricity-db-server \
  --sku-name B_Gen5_2 \
  --version 15
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Kubernetes logs
kubectl logs -f deployment/electricity-backend -n electricity-billing

# Export logs
kubectl logs deployment/electricity-backend -n electricity-billing > backend.log
```

### Backups

1. **Database Backup**
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres electricity_db > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 2 * * * docker-compose exec postgres pg_dump -U postgres electricity_db > /backups/backup_$(date +\%Y\%m\%d).sql
```

2. **Restore Database**
```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres electricity_db < backup_20240101.sql
```

3. **Model Backups**
```bash
# Backup ML models
tar -czf models_backup_$(date +%Y%m%d).tar.gz ml-models/models/

# Restore models
tar -xzf models_backup_20240101.tar.gz -C ml-models/
```

### Monitoring Dashboards

1. **Prometheus**
- URL: http://localhost:9090
- View metrics and alerts

2. **Grafana**
- URL: http://localhost:3001
- Default credentials: admin/admin
- Import dashboards from infrastructure/monitoring/grafana/

3. **Celery Flower**
- URL: http://localhost:5555
- Monitor background tasks

### Scaling

1. **Horizontal Scaling (Docker Compose)**
```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Scale celery workers
docker-compose up -d --scale celery-worker=5
```

2. **Kubernetes Horizontal Pod Autoscaler**
```bash
# Enable HPA
kubectl autoscale deployment electricity-backend \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n electricity-billing

# Check HPA status
kubectl get hpa -n electricity-billing
```

### Updates & Rollbacks

1. **Update Application**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Kubernetes rolling update
kubectl set image deployment/electricity-backend \
  electricity-backend=yourregistry/electricity-backend:v2.0 \
  -n electricity-billing
```

2. **Rollback**
```bash
# Docker Compose
docker-compose down
git checkout <previous-commit>
docker-compose up -d --build

# Kubernetes
kubectl rollout undo deployment/electricity-backend -n electricity-billing
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"

# Check logs
docker-compose logs postgres
```

2. **Redis Connection Errors**
```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Test connection
docker-compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
```

3. **ML Model Not Loading**
```bash
# Check if models exist
docker-compose exec backend ls -la models/

# Retrain models
docker-compose exec ml-trainer python training/train_all_models.py

# Check permissions
docker-compose exec backend chmod -R 755 models/
```

4. **High Memory Usage**
```bash
# Check resource usage
docker stats

# Increase memory limit in docker-compose.yml
services:
  backend:
    mem_limit: 2g
```

5. **Prediction Errors**
```bash
# Check if sufficient data exists
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.models import UsageData
db = SessionLocal()
count = db.query(UsageData).count()
print(f'Total usage records: {count}')
"

# Minimum 100 data points required for predictions
```

### Performance Optimization

1. **Database Query Optimization**
```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM usage_data WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 100;

-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_custom ON table_name(column_name);

-- Vacuum database
VACUUM ANALYZE;
```

2. **Redis Cache Tuning**
```bash
# Check cache hit rate
docker-compose exec redis redis-cli info stats | grep keyspace

# Clear cache if needed
docker-compose exec redis redis-cli FLUSHALL
```

3. **Application Performance**
```bash
# Enable profiling
docker-compose exec backend python -m cProfile -o profile.stats main.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

### Getting Help

- **GitHub Issues**: https://github.com/yourorg/electricity-billing-ai/issues
- **Documentation**: docs/
- **Email Support**: support@electricitybilling.ai
- **Community**: Discord/Slack channel

---

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Regular security updates
- [ ] Implement audit logging
- [ ] Use secrets management (Vault/AWS Secrets Manager)
- [ ] Enable database encryption
- [ ] Configure CORS properly
- [ ] Set up DDoS protection
- [ ] Implement API authentication
- [ ] Regular penetration testing

---

## License

This project is licensed under the MIT License - see LICENSE file for details.
