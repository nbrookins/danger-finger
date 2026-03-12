# AWS Deployment for Danger Finger -- Merged Final Plan

**Date**: 2026-03-11
**Status**: completed

## Goal

Enable reliable end-to-end testing in AWS with a repeatable, Terraform-managed deployment workflow. After local tests pass, a single `make deploy` pushes the containerized Tornado/OpenSCAD server to EC2, updates the Lambda read API, and verifies the deployment. The existing AWS account is audited and cleaned of stale resources. Cursor rules and skills make the process repeatable for future agent runs.

---

## Full Account Audit (completed 2026-03-12)

**Account**: 290552361409 | **Region**: us-east-1 primary

### Resources Found

**ECS Fargate (the "old running version")**
- CloudFormation stack `EC2ContainerService-danger1` (created 2020-02-03, "ECS Fargate First Run")
- ECS cluster `danger1`: ACTIVE but 0 running tasks
- Service `danger-finger-service`: desired=1, running=0. Last event: "unable to consistently start tasks successfully" (2026-03-11). Was failing to start because the Docker Hub image is from 2020.
- 3 task definitions all pulling `nbrookins/danger-finger` from **Docker Hub** (not ECR):
  - `danger-finger-api-small:1` -- 0.5 vCPU / 1GB
  - `danger-finger-api:2` -- 1 vCPU / 2GB
  - `danger-finger-api-2:1` -- 2 vCPU / 4GB
- ALB `EC2Co-EcsEl-QY18JTHYYHK1` -- ACTIVE, HTTP listener on :8081, **no targets registered**, DNS: `EC2Co-EcsEl-QY18JTHYYHK1-1448117639.us-east-1.elb.amazonaws.com`
- VPC `vpc-013a52aba94b58606` "ECS danger1" -- 10.0.0.0/16, 2 public subnets, IGW, route table
- Security groups: ALB SG (allow 8081 from 0.0.0.0/0), ECS SG (allow 1-65535 from ALB SG + 8081 from 0.0.0.0/0)

**Elastic IP**
- `107.21.46.243` (eipalloc-0c10f2984c0a8febc) -- **unassociated**, costing ~$3.65/mo

**IAM**
- User `danger-service`: S3FullAccess, 2 access keys (one active from 2025-12-16, one inactive from 2020-02-23)
- User `agent-admin`: AdministratorAccess (just created for this audit)
- Roles: `ecsAutoscaleRole`, `ecsTaskExecutionRole` (both from 2020 ECS setup)
- No custom policies

**S3**
- `danger-finger` (us-east-1, created 2020-02-23): 55 objects, ~17.7KB. Prefixes: configs/, downloads/, models/, preview/, profiles/, render/, scad/. All data from March 2020. **KEEP -- Terraform imports this.**
- `dc-os-test-exhibitors3bucket-b9sv3gvl0lsf` (us-west-1, created 2017-06-03): **EMPTY**, tagged with deleted CF stack. **DELETE.**

**Not present (clean)**
- No EC2 instances in any region
- No Lambda functions
- No API Gateway (v1 or v2)
- No Route53 hosted zones
- No ACM certificates
- No ECR repositories
- No NAT gateways
- No EBS volumes
- No key pairs
- Default VPC `vpc-964898ef` with 6 default subnets (leave alone)

### Current Monthly Cost (waste)
- ALB doing nothing: **~$16-22/mo**
- Unassociated Elastic IP: **~$3.65/mo**
- Total: **~$20-26/mo for zero benefit**

### Deployment History (from git archaeology)
- **Feb 2020**: Makefile/Docker template copied from SmartDrive Systems corporate infra (Harbor registry, Jenkins CI, OpsGenie heartbeats). None of that infra is relevant.
- **Feb 2020**: ECS Fargate cluster created via "First Run" wizard. Image pushed to Docker Hub as `nbrookins/danger-finger`. Service ran briefly.
- **Mar 2026**: Lambda handler and template.yaml created in recent agent session (commit c9a2511) but **never deployed** via SAM.
- The `DOCKER_REGISTRY ?= # harbor.smartdrivesystems.com/` in Makefile is a vestige.
- The `readUrl` in `web/app.js` is commented out with a placeholder -- Lambda was never live.

---

## Target Architecture

```mermaid
graph TB
    subgraph dns [Route53]
        domain["dangercreations.com"]
    end
    subgraph cert [ACM]
        acm["TLS Certificate"]
    end
    subgraph vpc [VPC]
        subgraph pubSubnet [Public Subnet]
            alb["ALB :443"]
            ec2["EC2 Instance :8081<br/>Docker + OpenSCAD"]
        end
    end
    subgraph serverless [Serverless]
        apigw["API Gateway<br/>Custom Domain"]
        lambda["Lambda<br/>S3 Read"]
    end
    subgraph storage [Storage]
        s3["S3 Bucket<br/>danger-finger"]
        ecr["ECR Repository"]
    end
    subgraph cicd [GitHub Actions]
        gha["Build + Test + Deploy"]
    end

    domain --> alb
    domain --> apigw
    acm --> alb
    acm --> apigw
    alb --> ec2
    ec2 -->|"write"| s3
    apigw --> lambda
    lambda -->|"read"| s3
    gha -->|"push image"| ecr
    gha -->|"deploy"| ec2
    ec2 -->|"pull image"| ecr
```

## Deployment Contract

- **Region**: us-east-1 (matches existing S3 bucket)
- **S3 Bucket**: `danger-finger` (existing, Terraform imports)
- **Docker image tag**: `danger-finger:{version}-{environ}-{git-sha}`
- **Container env vars**: `S3_BUCKET`, `AWS_REGION`, `READ_URL`
- **Lambda env vars**: `S3_BUCKET`
- **Resource tags**: `Project=danger-finger`, `Environment={dev|prod}`
- **Naming**: `danger-finger-{resource}`

---

## Phase 0: Account Cleanup

Delete everything that's costing money or serving no purpose. Safe order:

1. **Set ECS service desired count to 0** (stop launch attempts)
2. **Delete CloudFormation stack `EC2ContainerService-danger1`** -- this removes in one shot:
   - ALB + listener + target group (~$16-22/mo saved)
   - ECS security groups
   - VPC `vpc-013a52aba94b58606` + subnets + IGW + route table
3. **Release Elastic IP** `eipalloc-0c10f2984c0a8febc` ($3.65/mo saved)
4. **Delete ECS cluster `danger1`** and deregister all 3 task definitions
5. **Delete ECS IAM roles**: `ecsAutoscaleRole`, `ecsTaskExecutionRole`
6. **Delete S3 bucket `dc-os-test-exhibitors3bucket-b9sv3gvl0lsf`** (empty, us-west-1)
7. **Deactivate inactive `danger-service` key** `AKIAUHJSFGHAQLZBNFFO` (inactive since 2020)
8. **Clean up old S3 prefixes** in `danger-finger`: archive `downloads/`, `models/`, `preview/`, `scad/` (confirm not used by current code first)
9. **Verify**: re-run audit script to confirm clean state

**Do NOT delete**: S3 bucket `danger-finger`, IAM user `danger-service` (still used for local dev S3 writes), default VPC

---

## Phase 1: EC2 Instance Benchmark

OpenSCAD rendering is CPU-bound and historically single-threaded per file. The server runs 2 parallel renders (`max_concurrent_tasks=2`). The benchmark determines the best instance type for cost/performance.

### Benchmark methodology

Create `scripts/benchmark_ec2.py`:
1. Build Docker image and push to ECR (created in Phase 2)
2. For each candidate instance type, launch an EC2 instance with user data that:
   - Installs Docker
   - Pulls the image from ECR
   - Runs `python3 utility.py -r` (full render of all parts to STL)
   - Times the render and writes results to S3
   - Self-terminates
3. Collect results from S3, generate comparison table

### Candidate instances

```
Type             vCPUs  Mem(GB)   $/hr     $/mo    Notes
---------------------------------------------------------------
t3a.medium       2      4        $0.0376  $27     Cheapest viable, burstable
t3a.large        2      8        $0.0752  $55     More memory headroom
t3a.xlarge       4      16       $0.1504  $110    Test if 4 cores helps parallelism
c6a.large        2      4        $0.0765  $56     Dedicated compute (AMD EPYC)
c6a.xlarge       4      8        $0.1530  $112    Dedicated compute, 4 cores
c7a.large        2      4        $0.1026  $75     Latest AMD gen (Zen 4)
```

### What we're measuring
- **Full render time**: `python3 utility.py -r` (all SCAD -> STL for all parts)
- **Single preview time**: one preview render cycle (the critical path for user experience)
- **Memory usage peak**: ensure no OOM during render
- **Cost efficiency**: render-seconds per dollar

### Expected outcome
- t3a.medium is likely the sweet spot (2 vCPUs matches `max_concurrent_tasks=2`, cheapest)
- If renders are < 30s, burstable is fine (CPU credits won't deplete)
- If renders are > 60s sustained, c6a.large may be better (no credit depletion risk)

The benchmark runs as a one-time thing during initial setup. Results go into `docs/DEPLOY.md`.

---

## Phase 2: Terraform Foundation

### Directory structure

```
infra/
  main.tf            # Provider, S3 backend for state
  variables.tf       # Input variables (region, domain, instance type, etc.)
  outputs.tf         # API Gateway URL, EC2 IP, ALB DNS, ECR URI
  vpc.tf             # VPC, public subnet, IGW, route table, security groups
  ecr.tf             # ECR repository + lifecycle policy (keep last 10)
  ec2.tf             # EC2 instance, IAM instance profile, user data
  s3.tf              # Import existing bucket, enable versioning, bucket policy
  lambda.tf          # Lambda function + API Gateway HTTP API (replaces template.yaml)
  dns.tf             # Route53 zone/records, ACM cert, ALB
  terraform.tfvars   # Non-secret defaults
  environments/
    dev.tfvars
    prod.tfvars
```

### Bootstrap state backend
- S3 bucket: `danger-finger-tfstate` (versioned)
- DynamoDB table: `danger-finger-tflock`

### Core resources
- **VPC**: Single public subnet (reuse default VPC or new minimal one), SG (443 + SSH)
- **ECR**: `danger-finger` repo, lifecycle keeping 10 images
- **EC2**: Instance type from benchmark (likely t3a.medium), Amazon Linux 2023, IAM instance profile (S3 write + ECR pull), user data for Docker
- **S3**: Import `danger-finger`, enable versioning, bucket policy for Lambda
- **Lambda**: Convert template.yaml to Terraform. `aws_lambda_function` + `aws_apigatewayv2_api`. Package lambda/ as zip.
- **ALB**: HTTPS listener (ACM cert) -> EC2:8081
- **Route53**: A-record -> ALB, custom domain for API Gateway
- **ACM**: Cert for domain, DNS validation

### IAM changes
- EC2 instance profile replaces `aws_id`/`aws_key` env vars
- Small `web/server.py` change: fall back to default credential chain when no explicit keys
- Lambda role with S3 read-only (same as template.yaml)
- GitHub OIDC provider for Actions

### Frontend readUrl injection
- Add `READ_URL` env var to Docker container
- `web/server.py` injects value into `index.html` at serve time (`__READ_URL__` placeholder)
- `web/app.js` reads `window.__READ_URL__` or falls back to `baseurl`

---

## Phase 3: Deployment Automation

### Makefile targets
- `make ecr-login` -- Docker auth to ECR
- `make push-ecr` -- tag + push to ECR
- `make deploy-lambda` -- zip + update Lambda
- `make deploy-ec2` -- SSM Run Command to pull + restart container
- `make deploy` -- full pipeline with gates
- `make deploy-infra` -- terraform plan + apply
- `make test-deploy` -- e2e against deployed URL
- `make verify-aws` -- post-deploy smoke test
- `make audit-aws` -- account audit script
- `make benchmark-ec2` -- run instance benchmark

### Four-gate verification
1. **Pre-deploy**: `make test-web` + `make kbr-test` pass locally
2. **Deploy**: terraform plan clean, then apply
3. **Post-deploy**: smoke checks (EC2: health, preview, parts; Lambda: configs, profiles)
4. **Visual**: `make inspect-ui` against deployed URL

### GitHub Actions
- Trigger: push to main + workflow_dispatch
- Test -> Deploy -> Verify
- AWS auth via OIDC (no static keys)

---

## Phase 4: Rules and Skills

### Rule: `aws-deploy.mdc`
- Never commit credentials or secret .tfvars
- Run local tests before deploy
- Use `make deploy`, never Console changes
- Always `make verify-aws` after deploy
- EC2 uses IAM instance profiles

### Rule: `terraform-conventions.mdc`
- All infra through `infra/` Terraform
- Tag everything: Project, Environment
- Plan before apply
- Never edit state manually

### Skill: `deploy-to-aws/SKILL.md`
- First-time setup, deploy, rollback, debug, verify

---

## Phase 5: Documentation

- `docs/DEPLOY.md`: prerequisites, setup, workflow, benchmark results, troubleshooting
- Update `docs/PRODUCT.md`: architecture section
- Update `.gitignore`: Terraform files

---

## Files Affected

**New**: `infra/*.tf` (8), `infra/environments/*.tfvars` (2), `.github/workflows/deploy.yml`, `scripts/aws_audit.py`, `scripts/benchmark_ec2.py`, `scripts/verify_aws_deploy.sh`, `.cursor/rules/aws-deploy.mdc`, `.cursor/rules/terraform-conventions.mdc`, `.cursor/skills/deploy-to-aws/SKILL.md`, `docs/DEPLOY.md`

**Modified**: `Makefile`, `web/server.py`, `web/app.js`, `web/index.html`, `docker/env-example.txt`, `docs/PRODUCT.md`, `.gitignore`

**Removed**: `template.yaml` (after Terraform Lambda verified)

---

## Cleanup Savings Summary

| Resource | Current cost | After cleanup |
|----------|-------------|---------------|
| ALB (idle) | ~$16-22/mo | $0 (deleted with CF stack) |
| Elastic IP (unassociated) | ~$3.65/mo | $0 (released) |
| ECS Fargate (0 tasks) | $0 | $0 (deleted) |
| **Total waste** | **~$20-26/mo** | **$0** |

## New Infrastructure Cost Estimate

| Resource | Estimated cost |
|----------|---------------|
| EC2 t3a.medium (24/7) | ~$27/mo |
| ALB | ~$16-22/mo |
| S3 (minimal) | <$1/mo |
| Lambda (low volume) | <$1/mo |
| API Gateway | <$1/mo |
| Route53 zone | $0.50/mo |
| **Total** | **~$45-52/mo** |

## Open Questions
- Domain name -- is `dangercreations.com` already registered? In Route53?
- Whether to run EC2 24/7 or schedule stop/start (e.g., off at night) to save cost
- GitHub repo URL for Actions OIDC

## Outcome

**Completed 2026-03-12**

### What was done
- **Phase 0**: Cleaned up all stale resources. Deleted CloudFormation stack (required ENI cleanup for stuck SG/subnet), ECS cluster, 3 task definitions, 2 IAM roles, empty S3 bucket, deactivated old IAM key. Elastic IP was already released. Saves ~$20-26/mo.
- **Phase 1**: Created ECR repo, pushed Docker image. Benchmark script created but timed out at 15 min (image pull + render takes >15 min on fresh instances); proceeding with t3a.medium as default per analysis. Script available for re-run with `--timeout 2400`.
- **Phase 2**: Full Terraform infrastructure deployed — VPC (default), ECR, EC2 (t3a.medium), S3 (versioning enabled, public access blocked), Lambda + API Gateway (3 routes), IAM roles (EC2, Lambda, optional GitHub OIDC), conditional DNS/ACM. State backend bootstrapped (S3 + DynamoDB). Brotli Lambda layer built and deployed.
- **Phase 2d**: `web/server.py` updated for IAM credential fallback (uses default chain when no explicit keys). `READ_URL` injected into HTML via `window.__READ_URL__`. `web/app.js` reads it.
- **Phase 3**: Makefile targets added (ecr-login, push-ecr, deploy-lambda, deploy-ec2, deploy, deploy-infra, test-deploy, verify-aws, audit-aws, benchmark-ec2, echo-tag). GitHub Actions workflow created with OIDC auth.
- **Phase 4**: Rules created (aws-deploy.mdc, terraform-conventions.mdc). Skill created (deploy-to-aws/SKILL.md).
- **Phase 5**: docs/DEPLOY.md created. docs/PRODUCT.md updated with architecture section and changelog. .gitignore updated for Terraform files.

### Issues encountered
- Docker image built on Apple Silicon (ARM64) didn't work on EC2 (AMD64). Fixed with `docker buildx build --platform linux/amd64`.
- CloudFormation stack deletion failed on first attempt due to lingering ECS ENI. Fixed by deleting ENI manually then retrying.
- EC2 SSM agent required explicit `AmazonSSMManagedInstanceCore` policy on the IAM role — added to Terraform.
- Reboot interrupted user data script; had to manually deploy container via SSM.

### Deployed endpoints
- **EC2**: http://34.207.226.194:8081 (homepage, /api/parts, /api/preview)
- **API Gateway**: https://l68n2hu5re.execute-api.us-east-1.amazonaws.com/ (configs, profiles, bundles)

### Follow-ups
- Re-run benchmark with longer timeout (`--timeout 2400`) for actual performance data
- Add domain name and HTTPS (set `domain_name` and `enable_https` in tfvars)
- Configure GitHub OIDC (set `github_repo` in tfvars)
- Consider EC2 stop/start scheduling to reduce dev costs
- Update user_data.sh to use `--platform linux/amd64` in docker pull to be explicit
