# Audit Log (WORM, Tamper-Evident) Runbook

## Purpose

This runbook describes the operational procedures for managing the tamper-evident, immutable audit log system with S3 Object Lock and SHA-256 chaining.

---

## 1. Log Ingestion

- **Ingestor**: Fluent Bit (or Vector) collects logs from `/var/log/compliance/*.log`.
- **SHA Chaining**: Each log entry is chained to the previous using a Lua filter (`sha_chain.lua`).
- **Output**: Logs are written to S3 with Object Lock (COMPLIANCE mode, 7 years).

### Steps

1. Ensure Fluent Bit is running with the provided config.
2. Confirm logs are being written to S3 bucket with object lock enabled.
3. Monitor `/tmp/flb_last_sha` for last chain value (for continuity).

---

## 2. Immutable Storage (S3 Object Lock)

- **IaC**: Use Terraform (`terraform/main.tf`) to provision S3 bucket with Object Lock (COMPLIANCE mode).
- **Retention**: Default retention is 2555 days (7 years).
- **Versioning**: S3 bucket versioning is enabled.
- **Prevention**: `prevent_destroy = true` in Terraform to block accidental deletion.

### Steps

1. Deploy with `terraform apply` (set `bucket_name`, `region`).
2. Confirm bucket has Object Lock enabled in AWS Console.
3. All objects must show `ObjectLockMode: COMPLIANCE` and correct retention.

---

## 3. Verification

- **SHA Chain**: Use `verify_sha_chain.py` to check log file integrity.
- **S3 Object Lock**: Use `verify_s3_object_lock.sh` to check all objects for lock status.

### Steps

1. Download log file from S3 for verification.
2. Run `python3 verify_sha_chain.py <logfile>` to check SHA chain.
3. Run `./verify_s3_object_lock.sh <bucket> <prefix>` to check S3 lock status.

---

## 4. Incident Response

- **Tampering Detected**: If SHA chain breaks, escalate to security team immediately.
- **Object Lock Failure**: If any object is not locked, enable lock and investigate.
- **Legal Hold**: If required, set S3 object legal hold via AWS CLI or Console.

---

## 5. Maintenance

- **Key Rotation**: No keys to rotate for S3 lock, but rotate AWS credentials regularly.
- **Log Rotation**: Fluent Bit rotates logs to S3 every 5MB or 5 minutes.
- **Retention Review**: Review retention policy annually for compliance.

---

## 6. Recovery

- **Restore**: Download logs from S3 (read-only).
- **Audit**: Use verification tools to confirm integrity before use in investigations.

---

## 7. References

- [AWS S3 Object Lock Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [Fluent Bit Documentation](https://docs.fluentbit.io/manual/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_object_lock_configuration)
