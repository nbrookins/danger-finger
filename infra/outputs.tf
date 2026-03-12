output "ecr_repository_url" {
  description = "ECR repository URL for Docker images"
  value       = aws_ecr_repository.app.repository_url
}

output "ec2_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.app.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "s3_bucket" {
  description = "S3 bucket name"
  value       = data.aws_s3_bucket.app.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.s3_read.function_name
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL (Lambda read API)"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "app_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_instance.app.public_ip}:8081"
}

output "static_site_url" {
  description = "S3 static website URL (HTTP, for direct access or debugging)"
  value       = aws_s3_bucket_website_configuration.static.website_endpoint
}

output "static_site_https_url" {
  description = "CloudFront HTTPS URL for static site — use this for DANGERFINGER_APP_URL in WP wp-config.php"
  value       = "https://${aws_cloudfront_distribution.static.domain_name}"
}

output "static_bucket" {
  description = "S3 static website bucket name"
  value       = aws_s3_bucket.static.id
}
