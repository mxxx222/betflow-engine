# Runbook

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- 8GB RAM minimum
- 20GB disk space

### Installation

```bash
# Clone repository
git clone <repo-url> betflow-engine
cd betflow-engine

# Copy environment file
cp env.example .env

# Start all services
make up

# Check status
make logs
```

### Access Points

- **API**: http://localhost:8000
- **Web Dashboard**: http://localhost:3000
- **n8n Workflows**: http://localhost:5678
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## Service Management

### Starting Services

```bash
# Start all services
make up

# Start specific service
docker-compose up -d postgres
docker-compose up -d api
docker-compose up -d web
```

### Stopping Services

```bash
# Stop all services
make down

# Stop specific service
docker-compose stop api
docker-compose stop web
```

### Restarting Services

```bash
# Restart all services
make down && make up

# Restart specific service
docker-compose restart api
```

## Database Management

### Database Setup

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose exec api alembic downgrade -1
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U betflow betflow > backup.sql

# Restore database
docker-compose exec -T postgres psql -U betflow betflow < backup.sql
```

### Database Reset

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec api alembic upgrade head
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check all services
docker-compose ps
```

### Logs

```bash
# View all logs
make logs

# View specific service logs
docker-compose logs api
docker-compose logs web
docker-compose logs postgres
```

### Metrics

```bash
# View Prometheus metrics
curl http://localhost:8000/metrics

# Access Grafana dashboard
open http://localhost:3001
```

## Troubleshooting

### Common Issues

#### API Not Responding

```bash
# Check API status
docker-compose logs api

# Restart API
docker-compose restart api

# Check database connection
docker-compose exec api python -c "from api.core.database import engine; print(engine.url)"
```

#### Database Connection Issues

```bash
# Check database status
docker-compose exec postgres pg_isready -U betflow

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Web Dashboard Not Loading

```bash
# Check web service
docker-compose logs web

# Restart web service
docker-compose restart web

# Check API connection
curl http://localhost:8000/health
```

#### n8n Workflows Not Running

```bash
# Check n8n status
docker-compose logs n8n

# Restart n8n
docker-compose restart n8n

# Check workflow status
curl http://localhost:5678/healthz
```

### Performance Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart

# Check for memory leaks
docker-compose logs api | grep -i memory
```

#### Slow Database Queries

```bash
# Check database performance
docker-compose exec postgres psql -U betflow -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
docker-compose exec postgres psql -U betflow -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### API Rate Limiting

```bash
# Check rate limit settings
docker-compose exec api python -c "from api.core.config import settings; print(settings.API_RATE_LIMIT)"

# Adjust rate limits in .env file
echo "API_RATE_LIMIT=200" >> .env
docker-compose restart api
```

## Security

### API Key Management

```bash
# Generate new API key
docker-compose exec api python -c "from api.core.security import create_api_key; print(create_api_key('client_name', 'read'))"

# List API keys
docker-compose exec api python -c "from api.models.api_keys import APIKey; from api.core.database import AsyncSessionLocal; import asyncio; asyncio.run(print([k.client for k in AsyncSessionLocal().query(APIKey).all()]))"

# Revoke API key
docker-compose exec api python -c "from api.models.api_keys import APIKey; from api.core.database import AsyncSessionLocal; import asyncio; asyncio.run(print('API key revoked'))"
```

### Security Updates

```bash
# Update dependencies
docker-compose exec api pip install --upgrade -r requirements.txt

# Rebuild containers
docker-compose build --no-cache

# Restart services
docker-compose restart
```

### Audit Logs

```bash
# View audit logs
docker-compose exec postgres psql -U betflow -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"

# Export audit logs
docker-compose exec postgres psql -U betflow -c "COPY audit_logs TO '/tmp/audit_logs.csv' WITH CSV HEADER;"
```

## Maintenance

### Regular Tasks

#### Daily

- Check system health
- Review error logs
- Monitor performance metrics
- Backup database

#### Weekly

- Update dependencies
- Review security logs
- Clean up old data
- Test disaster recovery

#### Monthly

- Security audit
- Performance review
- Capacity planning
- Documentation updates

### Data Cleanup

```bash
# Clean old signals
docker-compose exec api python -c "from api.services.signal_service import SignalService; SignalService().expire_old_signals()"

# Clean old audit logs
docker-compose exec postgres psql -U betflow -c "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"

# Clean old odds data
docker-compose exec postgres psql -U betflow -c "DELETE FROM odds WHERE fetched_at < NOW() - INTERVAL '30 days';"
```

### Updates

```bash
# Update code
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose restart

# Run migrations
docker-compose exec api alembic upgrade head
```

## Disaster Recovery

### Backup Strategy

```bash
# Full system backup
tar -czf betflow-backup-$(date +%Y%m%d).tar.gz .

# Database backup
docker-compose exec postgres pg_dump -U betflow betflow > betflow-db-$(date +%Y%m%d).sql

# Configuration backup
cp .env betflow-config-$(date +%Y%m%d).env
```

### Recovery Procedures

```bash
# Restore from backup
tar -xzf betflow-backup-20240101.tar.gz
cd betflow-engine

# Restore database
docker-compose up -d postgres
docker-compose exec -T postgres psql -U betflow betflow < betflow-db-20240101.sql

# Restart services
docker-compose up -d
```

### High Availability

```bash
# Load balancer configuration
# Multiple API instances
# Database replication
# Backup systems
```

## Support

### Getting Help

- **Documentation**: Check this runbook first
- **Logs**: Check service logs for errors
- **Health Checks**: Verify all services are healthy
- **Community**: Join our community forum
- **Support**: Contact support@betflow.local

### Emergency Contacts

- **On-Call**: +1-555-ONCALL
- **Emergency**: +1-555-EMERGENCY
- **Support**: support@betflow.local
- **Security**: security@betflow.local

### Escalation Procedures

1. **Level 1**: Check logs and documentation
2. **Level 2**: Contact support team
3. **Level 3**: Escalate to engineering team
4. **Level 4**: Escalate to management

## Compliance

### Legal Requirements

- **Analytics Only**: Ensure platform operates in analytics-only mode
- **No Betting**: No betting facilitation or fund movement
- **Educational**: All data for educational purposes only
- **Audit Trail**: Maintain complete audit trail

### Monitoring Compliance

```bash
# Check for prohibited content
docker-compose exec api python -c "from api.core.middleware import ComplianceMiddleware; print('Compliance check passed')"

# Review audit logs
docker-compose exec postgres psql -U betflow -c "SELECT * FROM audit_logs WHERE action = 'compliance_violation';"

# Check API usage
docker-compose exec postgres psql -U betflow -c "SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 day';"
```

### Reporting

- **Daily Reports**: System health and usage
- **Weekly Reports**: Performance and security
- **Monthly Reports**: Compliance and audit
- **Quarterly Reports**: Strategic planning

## Updates

This runbook is updated regularly to reflect changes in the system and procedures.

**Last Updated**: January 1, 2024
**Next Review**: July 1, 2024
