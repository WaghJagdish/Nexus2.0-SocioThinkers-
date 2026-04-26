# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Code Quality
- [ ] All tests passing: `pytest --cov`
- [ ] No linting errors: `flake8 . --max-line-length=120`
- [ ] Type checking: `mypy .` (if configured)
- [ ] Security scan: `bandit -r .`
- [ ] Dependencies up to date: `pip list --outdated`

### 2. Documentation
- [ ] README.md updated with latest features
- [ ] API_DOCUMENTATION.yaml reflects all endpoints
- [ ] DEVELOPMENT_GUIDE.md reviewed for accuracy
- [ ] Environment variables documented
- [ ] Database schema documented

### 3. Configuration
- [ ] `.env.production` configured with prod secrets
- [ ] All API keys rotated and secure
- [ ] Database credentials in secure storage (AWS Secrets Manager, etc.)
- [ ] CORS origins restricted to production domain
- [ ] Rate limiting configured appropriately

### 4. Infrastructure
- [ ] Database backups configured (daily)
- [ ] Disk space adequate for logs and generated files
- [ ] Redis cache configured with persistence
- [ ] SSL/TLS certificates installed
- [ ] CDN configured for static assets

### 5. Monitoring & Logging
- [ ] CloudWatch/DataDog/New Relic configured
- [ ] Log aggregation set up
- [ ] Alerts configured for critical errors
- [ ] Metrics dashboard created
- [ ] Error tracking (Sentry) configured

### 6. Performance
- [ ] Database indexes created and optimized
- [ ] Query performance verified (< 100ms avg)
- [ ] Cache hit rates monitored (> 70% target)
- [ ] API response times acceptable (< 5s p95)

## Deployment Options

### Option 1: Docker on EC2 / Self-Hosted

**Step 1: Prepare Server**
```bash
# SSH into server
ssh -i key.pem ubuntu@server.example.com

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/nexus
sudo chown $USER:$USER /opt/nexus
```

**Step 2: Deploy Application**
```bash
# Copy files to server
scp -r -i key.pem ./backend_v2 ubuntu@server.example.com:/opt/nexus/

# Copy production .env
scp -i key.pem .env.production ubuntu@server.example.com:/opt/nexus/backend_v2/.env

# Deploy with docker-compose
cd /opt/nexus/backend_v2
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

**Step 3: Configure Reverse Proxy (Nginx)**
```nginx
upstream nexus_backend {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name api.nexus.example.com;

    ssl_certificate /etc/ssl/certs/nexus.crt;
    ssl_certificate_key /etc/ssl/private/nexus.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://nexus_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://nexus_backend/api/v1/health;
    }
}

server {
    listen 80;
    server_name api.nexus.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Option 2: AWS ECS (Elastic Container Service)

**Step 1: Push Docker Image to ECR**
```bash
# Create ECR repository
aws ecr create-repository --repository-name nexus-backend --region us-east-1

# Build and push image
docker build -t nexus-backend:2.0.0 .
docker tag nexus-backend:2.0.0 123456789.dkr.ecr.us-east-1.amazonaws.com/nexus-backend:2.0.0
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/nexus-backend:2.0.0
```

**Step 2: Create ECS Task Definition**
```json
{
  "family": "nexus-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "nexus-backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/nexus-backend:2.0.0",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "API_HOST", "value": "0.0.0.0"},
        {"name": "API_PORT", "value": "8000"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SARVAM_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SUPABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SUPABASE_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/nexus-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**Step 3: Create ECS Service**
```bash
aws ecs create-service \
  --cluster production \
  --service-name nexus-backend \
  --task-definition nexus-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=nexus-backend,containerPort=8000" \
  --region us-east-1
```

### Option 3: Heroku

**Step 1: Create Heroku App**
```bash
heroku create nexus-backend
heroku addons:create heroku-postgresql:standard-0 --app nexus-backend
heroku addons:create heroku-redis:premium-0 --app nexus-backend
```

**Step 2: Configure Procfile**
```
web: uvicorn main:create_app --host 0.0.0.0 --port $PORT --workers 4
```

**Step 3: Deploy**
```bash
git push heroku main
heroku logs --tail
```

## Post-Deployment Verification

### 1. Health Checks
```bash
# Test health endpoint
curl https://api.nexus.example.com/api/v1/health

# Expected response:
# {"status":"healthy","version":"2.0.0","services":{"database":"healthy","llm":"healthy","cache":"healthy"}}
```

### 2. API Tests
```bash
# Test text endpoint
curl -X POST https://api.nexus.example.com/api/v1/text/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "text": "What should I grow?",
    "latitude": 22.7196,
    "longitude": 75.8577,
    "device_language": "en"
  }'

# Test voice endpoint
curl -X POST https://api.nexus.example.com/api/v1/voice/sync \
  -F "audio_file=@test_audio.wav" \
  -F "user_id=test_user" \
  -F "device_language=hi"
```

### 3. Database Verification
```bash
# Connect to database
psql -h nexus-db.supabase.co -U postgres -d nexus_db

# Check tables created
SELECT tablename FROM pg_tables WHERE schemaname='public';

# Check data
SELECT COUNT(*) FROM farmers;
SELECT COUNT(*) FROM schemes;
```

### 4. Monitoring Setup
```bash
# View logs
docker-compose logs -f backend

# Monitor metrics
# - Dashboard: https://example.com/metrics
# - Alerts: Slack/Email for errors
```

## Scaling Strategies

### Horizontal Scaling

**Multiple Backend Instances:**
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    # Use load balancer to distribute traffic
```

**Load Balancer Configuration (HAProxy):**
```
global
    maxconn 4096

frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    server backend1 localhost:8001
    server backend2 localhost:8002
    server backend3 localhost:8003
    option httpchk GET /api/v1/health
```

### Vertical Scaling

**Increase Resources:**
```bash
# Docker: Increase memory/CPU in docker-compose.yml
resources:
  limits:
    cpus: '4'
    memory: 4G

# Kubernetes: Update resource requests
resources:
  requests:
    memory: "2Gi"
    cpu: "1"
  limits:
    memory: "4Gi"
    cpu: "2"
```

### Caching Layer

**Redis Clustering:**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --cluster-enabled yes
  deploy:
    replicas: 6
```

### Database Optimization

```sql
-- Read replicas
ALTER DATABASE nexus_db SET default_transaction_isolation TO 'read committed';

-- Connection pooling with PgBouncer
pgbouncer.ini:
  [databases]
  nexus_db = host=primary.rds.amazonaws.com port=5432 user=postgres password=xxx

-- Archive old interactions
DELETE FROM interactions 
WHERE created_at < NOW() - INTERVAL '1 year'
AND archived = true;
```

## Disaster Recovery

### Backup Strategy

```bash
# Daily backups
0 2 * * * /usr/local/bin/backup_nexus.sh

# backup_nexus.sh
#!/bin/bash
BACKUP_DIR=/backups/nexus
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -h nexus-db.supabase.co -U postgres nexus_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup generated files
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /opt/nexus/generated_pdfs /opt/nexus/generated_audio

# Upload to S3
aws s3 sync $BACKUP_DIR s3://nexus-backups/

# Cleanup old backups
find $BACKUP_DIR -mtime +30 -delete
```

### Recovery Procedure

```bash
# 1. Restore database
gunzip -c /backups/nexus/db_20240115_020000.sql.gz | psql -h nexus-db.supabase.co -U postgres nexus_db

# 2. Restore files
tar -xzf /backups/nexus/files_20240115_020000.tar.gz -C /

# 3. Verify integrity
curl https://api.nexus.example.com/api/v1/health

# 4. Monitor for issues
docker-compose logs -f backend
```

## Rollback Strategy

```bash
# 1. Keep previous version running
docker tag nexus-backend:2.0.0 nexus-backend:2.0.0-production
docker tag nexus-backend:2.0.0-hotfix nexus-backend:latest

# 2. Rollback command
docker pull nexus-backend:2.0.0-production
docker-compose down
docker-compose up -d

# 3. Verify
curl https://api.nexus.example.com/api/v1/health

# 4. Check logs
docker-compose logs backend
```

## Performance Tuning

### Database Query Optimization

```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM schemes 
  WHERE state = 'Madhya Pradesh' 
  AND category = 'agriculture';

-- Add missing indexes
CREATE INDEX idx_schemes_state_category ON schemes(state, category);

-- Vacuum and analyze
VACUUM ANALYZE;
```

### API Response Time Optimization

```python
# Use caching for frequently accessed data
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/v1/health"):
        response.headers["Cache-Control"] = "public, max-age=60"
    return response

# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check system resources
- Verify backups completed

**Weekly:**
- Review performance metrics
- Update security patches
- Test backup restoration

**Monthly:**
- Database optimization (VACUUM ANALYZE)
- Review and archive old data
- Update dependencies
- Security audit

## Support & Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.
