# Deploy to AWS

Deploy the danger-finger application to AWS infrastructure.

## Prerequisites

- AWS CLI configured with credentials (IAM user or OIDC)
- Docker installed and running
- Terraform 1.5+ installed (`brew install terraform`)
- Python 3.12+ with boto3

## First-time setup

```bash
# 1. Bootstrap Terraform state backend (one-time)
# Already done: S3 bucket danger-finger-tfstate + DynamoDB danger-finger-tflock

# 2. Initialize Terraform
cd infra && terraform init

# 3. Build and push Docker image
make build
make push-ecr

# 4. Deploy all infrastructure
make deploy-infra

# 5. Verify
make verify-aws
```

## Regular deployment

```bash
# Full pipeline: build → push → infra → verify
make deploy

# Container-only update (no infra changes)
make build && make push-ecr && make deploy-ec2

# Lambda-only update
make deploy-lambda

# Infrastructure-only
make deploy-infra
```

## Verification

```bash
# Smoke tests against deployed environment
make verify-aws

# Full audit of AWS account
make audit-aws
```

## Rollback

```bash
# Roll back to a specific image tag
cd infra
terraform apply -var docker_image_tag=5.3-dev-abc1234 -var-file=environments/dev.tfvars

# Roll back infrastructure
terraform plan -var-file=environments/dev.tfvars  # review changes
terraform apply -var-file=environments/dev.tfvars
```

## Debugging

```bash
# Check EC2 instance
aws ec2 describe-instances --filters "Name=tag:Project,Values=danger-finger" --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]'

# SSH into EC2 (if key pair configured)
ssh -i ~/.ssh/your-key.pem ec2-user@$(cd infra && terraform output -raw ec2_public_ip)

# Check container logs on EC2
aws ssm send-command --instance-ids $(cd infra && terraform output -raw ec2_instance_id) \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["docker logs danger-finger --tail 50"]'

# Check Lambda logs
aws logs tail /aws/lambda/danger-finger-s3-read --since 1h

# Test API Gateway directly
curl https://$(cd infra && terraform output -raw api_gateway_url)/configs/test
```

## Architecture

- **EC2 (t3a.medium)**: Runs Docker container with Tornado server + OpenSCAD. Handles writes to S3, serves web UI.
- **Lambda + API Gateway**: Read-only API for configs, profiles, bundle.zip from S3. Decouples reads from the render server.
- **S3 (danger-finger)**: Persistent storage for configs, profiles, rendered bundles.
- **ECR**: Docker image registry with lifecycle (keeps last 10).
- **Route53 + ACM**: Optional DNS + HTTPS (enable via `domain_name` and `enable_https` variables).

## Cost

| Resource | Est. monthly |
|----------|-------------|
| EC2 t3a.medium | ~$27 |
| S3 | <$1 |
| Lambda | <$1 |
| API Gateway | <$1 |
| Route53 (if enabled) | $0.50 |
| **Total** | **~$30** |
