# AWS Deployment Guide

## Architecture

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────┐
│   Browser    │──────▶│ EC2 (t3a.medium)  │──────▶│ S3 (writes) │
│              │       │ Docker + OpenSCAD  │       │             │
│              │       │ Tornado :8081      │       │             │
└──────────────┘       └──────────────────┘       └──────┬──────┘
       │                                                  │
       │  ┌─────────────────────┐                         │
       └──│ API Gateway (HTTP)  │──▶ Lambda ─────────────▶│ (reads)
          └─────────────────────┘                         │
                                                          │
          ┌──────────────┐                                │
          │ ECR (images) │◀── Docker push ────────────────┘
          └──────────────┘
```

- **EC2**: Runs the Docker container with Tornado web server + OpenSCAD renderer. Handles all writes to S3 (configs, profiles, rendered bundles). Serves the web UI.
- **Lambda + API Gateway**: Read-only serverless API for fetching configs, profiles, and bundle.zip from S3. Decouples reads from the compute-heavy render server.
- **S3 (`danger-finger`)**: Persistent storage for all project data.
- **ECR**: Docker image registry. Lifecycle policy keeps last 10 images.
- **Route53 + ACM**: Optional custom domain and HTTPS (not enabled by default).

## Prerequisites

- AWS CLI v2 configured (`aws configure`)
- Docker Desktop running
- Terraform 1.5+ (`brew install terraform`)
- Python 3.12+ with boto3 (`pip install boto3`)
- Make

## Quick Start

```bash
# First time: initialize Terraform
cd infra && terraform init && cd ..

# Full deploy: build → push to ECR → apply infra → verify
make deploy

# Verify deployment
make verify-aws
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make ecr-login` | Authenticate Docker to ECR |
| `make push-ecr` | Build, tag, and push Docker image to ECR |
| `make deploy-infra` | Terraform plan + apply |
| `make deploy-ec2` | Update container on EC2 (SSM) |
| `make deploy-lambda` | Update Lambda function code |
| `make deploy` | Full pipeline: build → push → infra |
| `make verify-aws` | Post-deploy smoke tests |
| `make audit-aws` | Full account audit |
| `make benchmark-ec2` | Run EC2 instance benchmark |

## Terraform Structure

```
infra/
  main.tf           — Provider, S3 backend
  variables.tf      — Input variables
  outputs.tf        — EC2 IP, API Gateway URL, etc.
  vpc.tf            — Default VPC, security groups
  ecr.tf            — ECR repository + lifecycle
  ec2.tf            — EC2 instance, IAM role, user data
  s3.tf             — S3 bucket config (versioning, access block)
  lambda.tf         — Lambda + API Gateway HTTP API
  dns.tf            — Route53, ACM (conditional)
  github_oidc.tf    — GitHub Actions OIDC (conditional)
  user_data.sh      — EC2 bootstrap script template
  environments/
    dev.tfvars      — Dev environment overrides
    prod.tfvars     — Prod environment overrides
```

## Environment Variables

### EC2 Container

| Variable | Description |
|----------|-------------|
| `S3_BUCKET` | S3 bucket name (default: `danger-finger`) |
| `AWS_DEFAULT_REGION` | AWS region (default: `us-east-1`) |
| `READ_URL` | API Gateway URL for Lambda read API |

### Lambda

| Variable | Description |
|----------|-------------|
| `S3_BUCKET` | S3 bucket name |

## IAM

- **EC2**: Uses an IAM instance profile with ECR pull + S3 read/write. No static keys needed.
- **Lambda**: Execution role with S3 read-only (GetObject, HeadObject).
- **GitHub Actions**: OIDC federation — no static keys in CI. Set `github_repo` in tfvars to enable.

## Cost Estimate

| Resource | Monthly cost |
|----------|-------------|
| EC2 t3a.medium (24/7) | ~$27 |
| S3 (minimal usage) | <$1 |
| Lambda (low volume) | <$1 |
| API Gateway | <$1 |
| Route53 zone (if enabled) | $0.50 |
| **Total** | **~$30** |

## Benchmarking

Run `make benchmark-ec2` or `python3 scripts/benchmark_ec2.py` to test instance types:

```bash
# Test specific types
python3 scripts/benchmark_ec2.py --types t3a.medium,c6a.large --timeout 2400

# Dry run (print user data script)
python3 scripts/benchmark_ec2.py --dry-run
```

### Benchmark results (2026-03-12, amd64, `latest` image)

| Type | Full render | Single part | Pull | $/hr | $/render | Score |
|------|-------------|-------------|------|------|----------|-------|
| t3a.medium | 40s | 3s | 42s | $0.0376 | $0.00042 | 0.418 ✓ best |
| c6a.large | 20s | 1s | 18s | $0.0765 | $0.00043 | 0.425 |
| c7a.large | 15s | 1s | 14s | $0.1026 | $0.00043 | 0.427 |
| t3a.xlarge | 34s | 2s | 29s | $0.1504 | $0.00142 | 1.420 |

**Score** = `($/hr × full_render_s / 3600) × 1000` — lower is cheaper per render.

**Recommendation**: `t3a.medium` wins on cost-per-render (all renders <45s = well within CPU credit burst window). Single-part preview is 3s on t3a.medium vs 1s on compute-optimized — negligible user-facing difference. The compute-optimized instances (c6a/c7a) offer faster absolute render times if UX latency is priority.

Note: `max_concurrent_tasks=2` in `scad_parallel()` is the **CLI batch rendering default** and does not affect web preview latency — web previews render parts sequentially (one per request). On a t3a.medium, a single tip preview takes ~3s end-to-end.

## Troubleshooting

### EC2 container not starting
```bash
# Check user data execution log
aws ssm send-command --instance-ids INSTANCE_ID --document-name AWS-RunShellScript \
  --parameters 'commands=["cat /var/log/cloud-init-output.log | tail -50"]'
```

### Lambda returning errors
```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/danger-finger-s3-read --since 1h
```

### Terraform state issues
```bash
# List state resources
cd infra && terraform state list

# Remove a resource from state (if manually deleted)
terraform state rm aws_instance.app
```

## CI/CD (GitHub Actions)

The `.github/workflows/deploy.yml` workflow:
1. **Test**: Build Docker image, run e2e tests
2. **Deploy**: Push to ECR, apply Terraform, update EC2 container
3. **Verify**: Run smoke tests against deployed environment

Requires:
- GitHub repository secret: `AWS_ACCOUNT_ID`
- OIDC: Set `github_repo` in Terraform to enable the IAM role
