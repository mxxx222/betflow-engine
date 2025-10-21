# Audit Log (WORM, Tamper-Evident)

This directory contains the implementation and documentation for a tamper-evident, immutable audit log system (WORM: Write Once, Read Many) with cryptographic SHA chaining.

## Components

- **Ingestor**: Fluent Bit/Vector configuration for log ingestion
- **Immutable Storage**: S3 Object Lock (WORM) with Terraform
- **Verification Tools**: Scripts for verifying SHA chain and log integrity
- **Runbook**: Operational procedures for audit log management

## Security Goals

- **Immutability**: Logs cannot be altered or deleted (WORM)
- **Tamper-Evidence**: Each log entry is chained with SHA-256 to previous entry
- **Centralization**: All critical events ingested to a single, protected log
- **Verifiability**: Automated tools to verify log chain and S3 object lock status

## Directory Structure

- `fluent-bit/` or `vector/`: Ingestor configs
- `terraform/`: S3 Object Lock infrastructure-as-code
- `verify/`: SHA chain and S3 verification scripts
- `runbook.md`: Operations and incident response
