resource "aws_s3_bucket" "model_bucket" {
    bucket = "${var.service_name}-${var.aws_account_number}"
    tags = var.tags
}

resource "aws_s3_bucket_versioning" "model_version" {
  bucket = aws_s3_bucket.model_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_bucket" {
    bucket = aws_s3_bucket.model_bucket.id
    rule {
      apply_server_side_encryption_by_default {
         sse_algorithm = "AES256"
      }
      bucket_key_enabled = false
    }
}

resource "aws_s3_bucket_public_access_block" "block_public_access_data_bucket" {
    bucket = aws_s3_bucket.model_bucket.id
    block_public_acls = true
    block_public_policy = true
    ignore_public_acls = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_acl" "model_bucket_acl" {
    bucket = aws_s3_bucket.model_bucket.id
    acl = "log-delivery-write"
}

resource "aws_s3_bucket_object" "model_version_prefix" {
    bucket = aws_s3_bucket.model_bucket.id
    key = "${var.version_prefix}/"
    tags = var.tags
}
