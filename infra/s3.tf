# Import the existing bucket rather than creating a new one.
# Run: terraform import aws_s3_bucket.app danger-finger (first time only)
data "aws_s3_bucket" "app" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "app" {
  bucket = data.aws_s3_bucket.app.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "app" {
  bucket = data.aws_s3_bucket.app.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
