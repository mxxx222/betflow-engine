#!/bin/bash
# Verifies S3 object lock status for all objects in the audit log bucket
# Usage: ./verify_s3_object_lock.sh <bucket-name> <prefix>

BUCKET="$1"
PREFIX="$2"

if [ -z "$BUCKET" ]; then
  echo "Usage: $0 <bucket-name> <prefix>"
  exit 1
fi

aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$PREFIX" --query 'Contents[].Key' --output text | while read key; do
  echo "Checking object: $key"
  lock=$(aws s3api get-object-retention --bucket "$BUCKET" --key "$key" 2>/dev/null)
  if echo "$lock" | grep -q 'COMPLIANCE'; then
    echo "  [OK] Object lock: COMPLIANCE"
  else
    echo "  [FAIL] Object lock missing or not COMPLIANCE"
  fi
  # Optionally, check legal hold
  hold=$(aws s3api get-object-legal-hold --bucket "$BUCKET" --key "$key" 2>/dev/null)
  if echo "$hold" | grep -q 'ON'; then
    echo "  [INFO] Legal hold: ON"
  fi
done