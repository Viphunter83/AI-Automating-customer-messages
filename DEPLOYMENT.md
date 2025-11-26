# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- OpenAI API Key (or ProxyAPI)
- SSL Certificate (for production)

## Local Development

```bash
docker-compose up
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Production Deployment

### 1. Prepare Environment

```bash
cp .env.production.example .env.production
# Edit .env.production with actual values
```

### 2. Generate SSL Certificate

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem -keyout ssl/key.pem -days 365
```

### 3. Run Production Compose

```bash
docker-compose -f docker-compose.prod.yml \
  --env-file .env.production up -d
```

### 4. Verify Health

```bash
curl https://yourdomain.com/health
```

## Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

## Monitoring

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- AlertManager: http://localhost:9093

## Backup

```bash
docker exec ai_support_db_prod pg_dump -U support_user ai_support \
  > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Updates

```bash
git pull origin main
docker-compose -f docker-compose.prod.yml \
  --env-file .env.production build
docker-compose -f docker-compose.prod.yml \
  --env-file .env.production up -d
```

