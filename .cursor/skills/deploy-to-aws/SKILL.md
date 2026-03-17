# Deploy to AWS

Deploy the danger-finger application to AWS infrastructure.

## Prerequisites

- AWS CLI configured with credentials (IAM user or OIDC)
- Docker installed and running (with Rosetta/QEMU for amd64 cross-compile on Apple Silicon)
- Terraform 1.5+ installed (`brew install terraform`)
- Python 3.12+ with boto3

## Regular deployment (recommended)

```bash
# Full pipeline: build (amd64) → push ECR → deploy EC2 → deploy static → health check
make deploy

# With JWT auth enabled (required for prod):
make deploy JWT_SECRET=your_secret
```

This runs the full chain. Each step verifies success before proceeding.

## Partial deploys

```bash
# Container-only update (code changes in server.py, Python, etc.)
make build && make push-ecr && make deploy-ec2

# Static-only update (HTML, JS, CSS changes)
make deploy-static
# Then invalidate CloudFront cache:
aws cloudfront create-invalidation --distribution-id E6P6W4VNARX5W --paths "/*"

# Lambda-only update
make deploy-lambda

# Infrastructure-only (terraform changes)
make deploy-infra
```

## Post-deploy verification

**Always verify through CloudFront** (`https://d1n87lopz9qnnf.cloudfront.net/`), not the raw EC2 IP.

```bash
# Health check
make check-health

# Full e2e preview test
JOB=$(curl -s -X POST https://d1n87lopz9qnnf.cloudfront.net/api/preview \
  -H "Content-Type: application/json" -d '{"params":{}}')
JOB_ID=$(echo "$JOB" | python3 -c "import json,sys; print(json.load(sys.stdin)['job_id'])")
sleep 10
curl -s "https://d1n87lopz9qnnf.cloudfront.net/api/jobs/$JOB_ID"
```

## Key architecture facts

- **`make build` cross-compiles to amd64** by default. Use `make build-native` for local testing.
- **`deploy-ec2` re-authenticates ECR** on the EC2 instance before pulling. No manual ECR login needed.
- **`deploy-ec2` waits for SSM completion** and reports success/failure (not fire-and-forget).
- **RENDER_URL points to CloudFront HTTPS**, not raw EC2 HTTP. CloudFront proxies `/api/*`, `/render/*`, `/profile/*`, `/params/*` to EC2.
- **All server routes must use `/api/` prefix** (or another prefix with a CloudFront behavior in `infra/static.tf`). Routes not covered by a behavior fall through to S3 and silently return `index.html`.

## Environment variables for deploy-ec2

| Variable | Source | Default |
|----------|--------|---------|
| `STATIC_SITE_URL` | `terraform output static_site_https_url` | `https://d1n87lopz9qnnf.cloudfront.net` |
| `APP_BASE_URL` | `terraform output app_url` | `http://<ec2-ip>:8081` |
| `WP_AUTH_URL` | Manual or GitHub secret | `https://dangercreations.com` |
| `JWT_SECRET` | Manual or GitHub secret | Empty (disables auth — dev mode) |

## Rollback

```bash
# Roll back to a specific image tag
cd infra
terraform apply -var docker_image_tag=5.4-dev-abc1234 -var-file=environments/dev.tfvars
```

## Debugging

```bash
# Check container logs on EC2
aws ssm send-command --instance-ids $(cd infra && terraform output -raw ec2_instance_id) \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["docker logs danger-finger --tail 50"]' \
  --region us-east-1

# Check Lambda logs
aws logs tail /aws/lambda/danger-finger-s3-read --since 1h

# Test API Gateway directly
curl "$(cd infra && terraform output -raw api_gateway_url)/configs/test"
```

## Cost

| Resource | Est. monthly |
|----------|-------------|
| EC2 t3a.medium | ~$27 |
| CloudFront | <$1 |
| S3 | <$1 |
| Lambda | <$1 |
| API Gateway | <$1 |
| **Total** | **~$30** |
