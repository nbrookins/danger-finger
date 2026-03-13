variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "danger-finger"
}

variable "domain_name" {
  description = "Domain name for the application (e.g. dangercreations.com)"
  type        = string
  default     = ""
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the application server (benchmark result)"
  type        = string
  default     = "t3a.medium"
}

variable "ec2_key_pair" {
  description = "EC2 key pair name for SSH access (optional)"
  type        = string
  default     = ""
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "s3_bucket_name" {
  description = "Existing S3 bucket name"
  type        = string
  default     = "danger-finger"
}

variable "enable_https" {
  description = "Enable HTTPS via ACM certificate (requires domain_name)"
  type        = bool
  default     = false
}

variable "github_repo" {
  description = "GitHub repository for OIDC (org/repo format)"
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Email address to subscribe to monitoring alerts (optional)"
  type        = string
  default     = ""
}
