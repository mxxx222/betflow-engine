# GDPR Compliance Data Flow Architecture

## Personal Data Classification

### Data Categories

```mermaid
graph TD
    A[Data Collection Points] --> B[Personal Data Categories]
    B --> C[Identity Data]
    B --> D[Technical Data]
    B --> E[Usage Data]
    B --> F[Location Data]

    C --> C1[Name, Email, UserID]
    D --> D1[IP Address, Device ID, MAC Address]
    E --> E1[Connection Logs, VPN Usage, Network Events]
    F --> F1[Geolocation, Network Location, Timezone]
```

### Data Processing Flow

```mermaid
flowchart TD
    Start([Data Collection]) --> Collect[Collection Points]

    Collect --> C1[Network Monitor]
    Collect --> C2[VPN Generator]
    Collect --> C3[Captive Portal Detector]
    Collect --> C4[API Integrations]

    C1 --> Process[Data Processing Layer]
    C2 --> Process
    C3 --> Process
    C4 --> Process

    Process --> Pseudo[Pseudonymization Engine]
    Pseudo --> Store[Encrypted Storage]

    Store --> S1[(Primary DB)]
    Store --> S2[(Audit Logs)]
    Store --> S3[(Backup Storage)]

    Process --> External[External Integrations]
    External --> E1[Notion API]
    External --> E2[Jira API]
    External --> E3[Google Drive API]

    Store --> Retention[Retention Manager]
    Retention --> R1[Scheduled Purge]
    Retention --> R2[Legal Hold]
    Retention --> R3[Data Subject Requests]

    R1 --> Delete[Secure Deletion]
    R3 --> Export[Data Export]

    style Pseudo fill:#e1f5fe
    style Store fill:#f3e5f5
    style External fill:#fff3e0
    style Retention fill:#e8f5e8
```

## GDPR Article 25: Data Protection by Design

### Technical Measures

```mermaid
graph LR
    A[Data Protection by Design] --> B[Pseudonymization]
    A --> C[Encryption at Rest]
    A --> D[Encryption in Transit]
    A --> E[Access Control]
    A --> F[Audit Logging]
    A --> G[Data Minimization]

    B --> B1[Reversible Hashing]
    B --> B2[Format Preserving Encryption]
    B --> B3[Key Rotation]

    C --> C1[AES-256 Database Encryption]
    C --> C2[Encrypted File Storage]

    D --> D1[TLS 1.3 API Calls]
    D --> D2[WireGuard VPN Tunnels]

    E --> E1[RBAC Implementation]
    E --> E2[Multi-Factor Authentication]
    E --> E3[Principle of Least Privilege]

    F --> F1[Immutable Audit Trail]
    F --> F2[Compliance Monitoring]

    G --> G1[Purpose Limitation]
    G --> G2[Storage Limitation]
```

### Data Subject Rights Implementation

```mermaid
sequenceDiagram
    participant DS as Data Subject
    participant API as Privacy API
    participant Auth as Authentication
    participant DB as Database
    participant Pseudo as Pseudonymization
    participant Audit as Audit System

    Note over DS,Audit: Right of Access (Art. 15)
    DS->>API: Request Personal Data Export
    API->>Auth: Verify Identity
    Auth->>API: Authentication Token
    API->>DB: Query Personal Data
    DB->>Pseudo: Decrypt/De-pseudonymize
    Pseudo->>API: Readable Data
    API->>DS: Export Package
    API->>Audit: Log Access Request

    Note over DS,Audit: Right to Rectification (Art. 16)
    DS->>API: Request Data Correction
    API->>Auth: Verify Identity
    API->>DB: Update Records
    DB->>Pseudo: Re-encrypt Updated Data
    API->>Audit: Log Rectification

    Note over DS,Audit: Right to Erasure (Art. 17)
    DS->>API: Request Data Deletion
    API->>Auth: Verify Identity
    API->>DB: Check Legal Obligations
    DB->>DB: Secure Deletion
    DB->>API: Deletion Confirmation
    API->>Audit: Log Erasure Request
```

## Integration Security Architecture

### External API Data Flow

```mermaid
graph TD
    A[Net-Sec Application] --> B[API Gateway]
    B --> C[Authentication Layer]
    C --> D[Data Minimization Filter]
    D --> E[Encryption Proxy]

    E --> F1[Notion API]
    E --> F2[Jira API]
    E --> F3[Google Drive API]

    F1 --> G[Response Handler]
    F2 --> G
    F3 --> G

    G --> H[Data Classification]
    H --> I[Pseudonymization]
    I --> J[Encrypted Storage]

    J --> K[Audit Trail]
    K --> L[Compliance Monitor]

    style C fill:#ffcdd2
    style D fill:#e1f5fe
    style I fill:#f3e5f5
    style K fill:#e8f5e8
```

### Audit Trail Requirements

```mermaid
graph LR
    A[System Events] --> B[Audit Collector]
    B --> C[Event Classification]

    C --> D1[Data Access Events]
    C --> D2[Processing Events]
    C --> D3[Integration Events]
    C --> D4[Admin Events]

    D1 --> E[Structured Logging]
    D2 --> E
    D3 --> E
    D4 --> E

    E --> F[Immutable Storage]
    F --> G[Compliance Reports]
    F --> H[Alert System]

    G --> I[GDPR Compliance Report]
    G --> J[Data Protection Impact Assessment]
    G --> K[Breach Notification System]
```

## Retention Policy Framework

### Data Lifecycle Management

```mermaid
gantt
    title Data Retention Lifecycle
    dateFormat  YYYY-MM-DD
    section Collection Phase
    Data Ingestion           :active, collect, 2025-01-01, 30d
    section Processing Phase
    Pseudonymization        :process, after collect, 30d
    Purpose-bound Processing :purpose, after process, 90d
    section Storage Phase
    Active Storage          :storage, after purpose, 365d
    Archive Storage         :archive, after storage, 1095d
    section Disposal Phase
    Scheduled Review        :review, after archive, 30d
    Secure Deletion         :delete, after review, 7d
```

### Retention Rules by Data Type

```yaml
retention_policies:
  network_logs:
    retention_period: "12 months"
    purge_method: "secure_deletion"
    legal_hold_applicable: true

  user_preferences:
    retention_period: "24 months"
    purge_method: "anonymization"
    legal_hold_applicable: false

  authentication_logs:
    retention_period: "36 months"
    purge_method: "secure_deletion"
    legal_hold_applicable: true

  api_integration_data:
    retention_period: "6 months"
    purge_method: "complete_removal"
    legal_hold_applicable: false

  audit_trails:
    retention_period: "84 months"
    purge_method: "never" # Regulatory requirement
    legal_hold_applicable: true
```

## Privacy Controls Matrix

| Data Type        | Collection Basis    | Purpose             | Retention        | Subject Rights        | Security Level |
| ---------------- | ------------------- | ------------------- | ---------------- | --------------------- | -------------- |
| Network Metadata | Legitimate Interest | Service Operation   | 12 months        | Access, Portability   | High           |
| User Credentials | Contract            | Authentication      | Account Lifetime | Access, Rectification | Critical       |
| Usage Analytics  | Consent             | Service Improvement | 6 months         | Access, Withdrawal    | Medium         |
| Integration Data | Consent             | Feature Enhancement | 3 months         | Access, Erasure       | High           |
| Audit Logs       | Legal Obligation    | Compliance          | 7 years          | Access (Limited)      | Critical       |
| Backup Data      | Legitimate Interest | Disaster Recovery   | Same as Primary  | Same as Primary       | Critical       |

## Implementation Priorities

### Phase 1: Core Infrastructure (Weeks 1-2)

- [ ] Pseudonymization library implementation
- [ ] Database encryption setup
- [ ] Basic audit logging
- [ ] RBAC foundation

### Phase 2: GDPR Compliance (Weeks 3-4)

- [ ] Data subject rights API
- [ ] Retention policy engine
- [ ] Consent management
- [ ] Privacy dashboard

### Phase 3: External Integrations (Weeks 5-6)

- [ ] Secure API connectors
- [ ] Data minimization filters
- [ ] Integration audit trails
- [ ] Breach detection system

### Phase 4: Monitoring & Automation (Weeks 7-8)

- [ ] Compliance monitoring dashboard
- [ ] Automated retention jobs
- [ ] Alert systems
- [ ] Compliance reporting

## Legal Basis Documentation

### Article 6 GDPR - Lawfulness of Processing

```yaml
legal_bases:
  network_monitoring:
    basis: "legitimate_interest"
    assessment: "Network security and service stability"
    balancing_test: "User privacy vs. security necessity"

  user_authentication:
    basis: "contract"
    necessity: "Service delivery requirement"

  analytics_data:
    basis: "consent"
    consent_mechanism: "Granular opt-in"
    withdrawal_method: "One-click revocation"

  compliance_logging:
    basis: "legal_obligation"
    regulatory_source: "eIDAS, NIS2, GDPR Article 5(2)"
```

This comprehensive data flow architecture ensures GDPR compliance while maintaining the security functionality of the net-sec tool. Next, I'll implement the pseudonymization library.
