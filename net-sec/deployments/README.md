# GDPR Compliance System - Infrastructure as Code

This directory contains Docker, Kubernetes, and monitoring configurations for deploying the GDPR compliance system.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  Privacy Gateway │────│  Compliance API │
│     (Nginx)     │    │   (Rate Limit)   │    │   (Go Service)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                       ┌────────▼────────┐              │
                       │  Audit Service  │              │
                       │   (Immutable)   │              │
                       └─────────────────┘              │
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌────────▼────────┐
│   PostgreSQL    │────│  Redis Cache     │────│  Key Management │
│ (Encrypted DB)  │    │  (Sessions)      │    │    (Vault)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### Core Services

- **Privacy Gateway**: Rate limiting, TLS termination, request routing
- **Compliance API**: Main GDPR compliance service
- **Key Management**: Cryptographic key lifecycle management
- **Audit Service**: Immutable audit logging
- **Retention Jobs**: Automated data purging

### Storage

- **PostgreSQL**: Encrypted primary database with GDPR data classification
- **Redis**: Session storage and caching layer
- **Vault**: Secure key management and secrets

### Monitoring

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Compliance dashboards and visualization
- **Jaeger**: Distributed tracing for audit trails
- **ELK Stack**: Log aggregation and search

## Security Features

### Encryption

- TLS 1.3 for all external communications
- Database encryption at rest using AES-256
- Key rotation every 24 hours
- Perfect forward secrecy

### Network Security

- Network policies isolating services
- Private subnets for sensitive components
- WAF rules for API protection
- DDoS protection

### Compliance Controls

- Automated GDPR compliance monitoring
- Real-time data breach detection
- Automated retention policy enforcement
- Privacy-by-design architecture

## Deployment Environments

### Development

- Local Docker Compose setup
- Test data with synthetic PII
- Debug logging enabled
- Relaxed security for development

### Staging

- Kubernetes deployment
- Production-like data (pseudonymized)
- Full audit logging
- Performance testing

### Production

- Multi-region Kubernetes clusters
- High availability configuration
- Full encryption and monitoring
- Automated backup and recovery

## Getting Started

1. **Prerequisites**

   ```bash
   docker >= 20.10
   kubectl >= 1.24
   helm >= 3.8
   ```

2. **Local Development**

   ```bash
   docker-compose up -d
   ```

3. **Staging/Production**
   ```bash
   helm install gdpr-compliance ./helm/gdpr-compliance
   ```

## Configuration

All configuration is managed through environment variables and Kubernetes ConfigMaps/Secrets.

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/gdpr_compliance?sslmode=require

# Encryption
ENCRYPTION_KEY_ID=primary-2024
VAULT_ADDR=https://vault.internal:8200
VAULT_TOKEN=<vault-token>

# External APIs
NOTION_API_TOKEN=<notion-token>
JIRA_API_TOKEN=<jira-token>
GOOGLE_SERVICE_ACCOUNT_KEY=<base64-encoded-key>

# Monitoring
PROMETHEUS_URL=https://prometheus.internal:9090
JAEGER_ENDPOINT=https://jaeger.internal:14268

# GDPR Configuration
DEFAULT_RETENTION_PERIOD=2y
PSEUDONYMIZATION_ENABLED=true
DATA_MINIMIZATION_ENABLED=true
AUDIT_ALL_ACCESS=true
```

## Monitoring and Alerting

### Key Metrics

- **Data Processing Compliance**: % of operations following GDPR procedures
- **Retention Policy Compliance**: % of data within retention periods
- **Access Control Violations**: Unauthorized access attempts
- **Key Rotation Success**: Cryptographic key rotation health
- **Response Times**: API performance metrics

### Critical Alerts

- Data breach detection
- Failed key rotations
- Retention policy violations
- RBAC violations
- Service availability issues

## Backup and Recovery

### Automated Backups

- Database backups every 4 hours
- Key material backups (encrypted)
- Configuration backups
- Audit log backups (immutable)

### Recovery Procedures

- RTO: < 4 hours
- RPO: < 1 hour
- Automated failover for critical components
- Manual approval for data restoration

## Compliance Reporting

### Automated Reports

- Weekly compliance status reports
- Monthly data processing reports
- Quarterly GDPR assessment reports
- Real-time breach notifications

### Report Distribution

- Data Protection Officer (DPO)
- Legal team
- Security team
- Executive leadership

## Maintenance

### Regular Tasks

- Security patches (automated)
- Certificate renewal (automated)
- Key rotation monitoring
- Compliance metric review

### Scheduled Maintenance

- Database maintenance windows
- Infrastructure updates
- Security assessments
- Compliance audits

## Troubleshooting

### Common Issues

1. **Key Rotation Failures**: Check Vault connectivity and permissions
2. **Database Connection Issues**: Verify encryption and network policies
3. **External API Rate Limits**: Review rate limiting configuration
4. **Audit Log Issues**: Check immutable storage availability

### Debug Commands

```bash
# Check service health
kubectl get pods -n gdpr-compliance

# View service logs
kubectl logs -f deployment/compliance-api -n gdpr-compliance

# Check metrics
curl http://localhost:9090/metrics

# Test key rotation
curl -X POST http://localhost:8080/admin/rotate-keys
```

## Security Contacts

- **Security Team**: security@company.com
- **Data Protection Officer**: dpo@company.com
- **Emergency**: security-emergency@company.com

## Documentation

- [API Documentation](./docs/api.md)
- [Security Architecture](./docs/security.md)
- [GDPR Compliance Guide](./docs/gdpr-compliance.md)
- [Runbook](./docs/runbook.md)
