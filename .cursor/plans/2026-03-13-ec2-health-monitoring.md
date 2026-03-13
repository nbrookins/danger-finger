# EC2 Health Monitoring

**Date**: 2026-03-13
**Status**: completed

## Goal
Add a lightweight monitoring and recovery layer for the single-EC2 deployment so the project can detect when the render server is unavailable, attempt an automatic restart, and alert the owner when automatic recovery is not sufficient.

## Steps
1. Add Terraform resources for SNS alerting, EC2 status-check alarms, scheduled health checks, and Lambda/SSM IAM permissions.
2. Create a health-check Lambda that probes the Tornado app, records a custom metric, and attempts a container restart via SSM on failure.
3. Add Terraform variables/outputs and Makefile helpers for monitoring configuration and manual checks.
4. Update deployment documentation with setup, alert subscription, troubleshooting, and verification steps.
5. Validate Python/Terraform changes and note any apply-time prerequisites.

## Key decisions
- Use AWS-native EC2 auto-recovery for instance-level failures and a small Lambda for application-level failures.
- Use CloudWatch alarms to drive SNS notifications so alerting stays centralized and avoids duplicate notification paths.
- Probe `GET /api/parts` because it exercises the render server without triggering expensive render work.
- Keep the first version single-instance aware; do not design for ASG/multi-instance until the deployment model changes.

## Files affected
- `infra/monitoring.tf` — new monitoring infrastructure resources
- `infra/variables.tf` — alert email input
- `infra/outputs.tf` — monitoring outputs
- `lambda/health_check.py` — probe/restart Lambda
- `Makefile` — manual health-check commands
- `docs/DEPLOY.md` — monitoring setup and operations
- `docs/PRODUCT.md` — changelog / user-facing architecture note

## Outcome
Implemented the monitoring stack in Terraform and Lambda. The repo now includes SNS alerting, EC2 system recovery, a scheduled app health-check Lambda with SSM restart attempts, new operator Make targets, and deployment/docs updates. Local verification passed for `python3 -m py_compile lambda/health_check.py` and `terraform validate`; `terraform fmt` also normalized the changed Terraform files. Apply-time prerequisite: set `alert_email` if email alerts are desired, then confirm the SNS subscription email after `terraform apply`.
