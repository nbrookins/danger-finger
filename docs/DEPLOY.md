# AWS Deployment Guide

## Architecture

```
                              ┌──────────────────────────────┐
┌──────────────┐  HTML/JS/CSS │ S3 static site (always on)   │
│   Browser    │◀────────────▶│ danger-finger-static          │
│              │              └──────────────────────────────┘
│              │
│              │  render POST  ┌──────────────────┐       ┌─────────────┐
│              │──────────────▶│ EC2 (t3a.medium)  │──────▶│ S3 (writes) │
│              │  (can fail)   │ Docker + OpenSCAD  │       │             │
│              │               │ Tornado :8081      │       │             │
└──────────────┘               └──────────────────┘       └──────┬──────┘
       │                                                          │
       │  configs/profiles  ┌─────────────────────┐               │
       └───────────────────▶│ API Gateway (HTTP)  │──▶ Lambda ───▶│ (reads)
                            └─────────────────────┘               │
                                                                  │
          ┌──────────────┐                                        │
          │ ECR (images) │◀── Docker push ────────────────────────┘
          └──────────────┘
```

- **S3 static site (`danger-finger-static`)**: Always-on frontend. Serves HTML, JS, CSS, and baked-in JSON for parts/params. If EC2 is down, the UI still loads and all read features work.
- **EC2**: Runs the Docker container with Tornado web server + OpenSCAD renderer. Handles render API calls (POST /api/preview, /api/render) and writes to S3.
- **Lambda + API Gateway**: Read-only serverless API for fetching configs, profiles, and bundle.zip from S3. Always available.
- **S3 (`danger-finger`)**: Persistent storage for all project data (configs, profiles, rendered bundles).
- **ECR**: Docker image registry. Lifecycle policy keeps last 10 images.
- **Route53 + ACM**: Optional custom domain and HTTPS (not enabled by default).

### Static site URLs

| Endpoint | URL | Use |
|----------|-----|-----|
| CloudFront (HTTPS) | `https://d1n87lopz9qnnf.cloudfront.net` | Primary — use this for `DANGERFINGER_APP_URL` in WordPress wp-config.php. Required to avoid mixed-content blocking inside the HTTPS WP page. |
| S3 website (HTTP) | `http://danger-finger-static.s3-website-us-east-1.amazonaws.com` | Direct / debugging only |

The static site is the primary frontend. It loads without EC2. Preview/render calls go to EC2 and degrade gracefully with a "server offline" message when EC2 is down.

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
| `make check-health` | Hit the render server health endpoint directly |
| `make check-monitoring` | Show current CloudWatch alarm states |
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

### Monitoring / Terraform

| Variable | Description |
|----------|-------------|
| `alert_email` | Email address subscribed to SNS monitoring alerts (optional) |

## IAM

- **EC2**: Uses an IAM instance profile with ECR pull + S3 read/write. No static keys needed.
- **Lambda**: Execution role with S3 read-only (GetObject, HeadObject).
- **GitHub Actions**: OIDC federation — no static keys in CI. Set `github_repo` in tfvars to enable.

## Cost Estimate

| Resource | Monthly cost |
|----------|-------------|
| EC2 t3a.medium (24/7) | ~$27 |
| S3 data bucket (minimal usage) | <$1 |
| S3 static site bucket | <$0.01 |
| Lambda (low volume) | <$1 |
| API Gateway | <$1 |
| Route53 zone (if enabled) | $0.50 |
| **Total** | **~$30** |

## Static Site Deployment

The frontend is served from S3 static website hosting. This provides always-on availability independent of EC2.

```bash
# Generate static JSON + deploy to S3
make deploy-static

# Specify custom URLs (otherwise reads from Terraform outputs)
make deploy-static READ_URL=https://YOUR_API_GW.amazonaws.com RENDER_URL=http://EC2_IP:8081/
```

When EC2 is down, the static site still loads and all read features (configs, profiles, parameter controls) work via Lambda. Only preview/render shows "server offline".

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

### Monitoring and auto-recovery

The monitoring stack has two layers:

1. **EC2 system recovery** — CloudWatch alarms on `StatusCheckFailed_System` trigger AWS auto-recovery and send an SNS alert.
2. **Application health check** — a scheduled Lambda hits `GET /api/parts` every 5 minutes. If the request fails twice in a row, CloudWatch alarms send an alert. On each failing invocation, the Lambda attempts `docker restart danger-finger` via SSM.

Setup notes:
- Set `alert_email` in your Terraform variables before applying if you want email alerts.
- After the first apply, AWS SNS sends a subscription-confirmation email. Alerts do not flow until you confirm it.
- The health-check Lambda is intentionally lightweight: it probes the app endpoint without triggering a render job.

Operator commands:

```bash
# Check app health directly
make check-health

# Inspect CloudWatch alarm states
make check-monitoring

# Read health-check Lambda logs
aws --region us-east-1 logs tail /aws/lambda/danger-finger-health-check --since 1h
```

Failure behavior:
- If the EC2 host fails AWS system checks, AWS attempts instance recovery automatically.
- If the instance is up but Tornado/container is unhealthy, the scheduled Lambda attempts a restart through SSM.
- If the app stays unhealthy across consecutive checks, CloudWatch triggers the SNS alert and manual intervention is needed.

### Guest access and render recovery

The configurator now supports anonymous preview and anonymous render submission. Profile saves still require login.

Operational details:
- Full renders are queued as durable job records under `jobs/{job_id}` and mirrored to `render/{cfghash}/status` for hash-based polling.
- Authenticated jobs are dispatched ahead of guest jobs; guests are also rate-limited.
- On restart, the Tornado server scans queued/running jobs and requeues interrupted work. Recovery is whole-job requeue only; it does not resume partial OpenSCAD output mid-file.
- Bundle existence at `render/{cfghash}/bundle.zip` is the final source of truth for completion and dedupe.

Verification notes:
- Verify guest access from the WordPress wrapper, not just the raw app URL.
- Verify that a guest save click redirects to login and restores the draft after JWT callback.
- If testing restart recovery, kill the Tornado process during a queued/running render, let watchdog restart it, then poll the job/status endpoint until it resumes or completes.

## CI/CD (GitHub Actions)

The `.github/workflows/deploy.yml` workflow:
1. **Test**: Build Docker image, run e2e tests
2. **Deploy**: Push to ECR, apply Terraform, update EC2 container
3. **Verify**: Run smoke tests against deployed environment

Requires:
- GitHub repository secret: `AWS_ACCOUNT_ID`
- OIDC: Set `github_repo` in Terraform to enable the IAM role
