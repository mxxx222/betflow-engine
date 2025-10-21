terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
  required_version = ">= 1.3"
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "audit_log" {
  bucket = var.bucket_name
  force_destroy = false

  object_lock_configuration {
    object_lock_enabled = "Enabled"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "audit_log_versioning" {
  bucket = aws_s3_bucket.audit_log.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "audit_log_lock" {
  bucket = aws_s3_bucket.audit_log.id
  rule {
    default_retention {
      mode  = "COMPLIANCE"
      days  = var.object_lock_days
    }
  }
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for audit log"
  type        = string
}

variable "object_lock_days" {
  description = "Retention period in days for object lock"
  type        = number
  default     = 2555 # 7 years
}
