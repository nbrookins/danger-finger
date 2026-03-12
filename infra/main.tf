terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "danger-finger-tfstate"
    key            = "danger-finger/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "danger-finger-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "danger-finger"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
