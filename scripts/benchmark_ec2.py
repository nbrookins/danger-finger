#!/usr/bin/env python3
"""EC2 instance benchmark for OpenSCAD rendering workloads.

Launches one instance per candidate type, runs a full render (utility.py -r)
inside the Docker container, writes timing to S3, and self-terminates.
Results are collected and printed as a cost/performance comparison table.

Usage:
    python3 scripts/benchmark_ec2.py [--dry-run] [--types t3a.medium,c6a.large]
"""
import argparse
import base64
import json
import sys
import time

import boto3

REGION = "us-east-1"
ECR_REPO = "danger-finger"
ECR_TAG = "latest"
S3_BUCKET = "danger-finger"
S3_PREFIX = "benchmark/"
PROJECT_TAG = "danger-finger"

DEFAULT_INSTANCE_TYPES = [
    "t3a.medium",
    "t3a.xlarge",
    "c6a.large",
    "c7a.large",
]

HOURLY_COST = {
    "t3a.medium": 0.0376,
    "t3a.large": 0.0752,
    "t3a.xlarge": 0.1504,
    "c6a.large": 0.0765,
    "c6a.xlarge": 0.1530,
    "c7a.large": 0.1026,
}

ROLE_NAME = "danger-finger-benchmark-role"
PROFILE_NAME = "danger-finger-benchmark-profile"
SG_NAME = "danger-finger-benchmark-sg"


def get_account_id(session):
    return session.client("sts").get_caller_identity()["Account"]


def get_latest_al2023_ami(ec2):
    ssm = boto3.client("ssm", region_name=REGION)
    resp = ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64")
    return resp["Parameter"]["Value"]


def ensure_iam_role(iam, account_id):
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })
    inline_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability",
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject"],
                "Resource": f"arn:aws:s3:::{S3_BUCKET}/{S3_PREFIX}*"
            },
            {
                "Effect": "Allow",
                "Action": ["ec2:TerminateInstances"],
                "Resource": "*",
                "Condition": {"StringEquals": {"aws:ResourceTag/Purpose": "benchmark"}}
            },
        ]
    })
    try:
        iam.get_role(RoleName=ROLE_NAME)
        print(f"  IAM role {ROLE_NAME} already exists")
    except iam.exceptions.NoSuchEntityException:
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=trust_policy,
                        Tags=[{"Key": "Project", "Value": PROJECT_TAG}])
        print(f"  Created IAM role {ROLE_NAME}")

    iam.put_role_policy(RoleName=ROLE_NAME, PolicyName="benchmark-policy", PolicyDocument=inline_policy)

    try:
        iam.get_instance_profile(InstanceProfileName=PROFILE_NAME)
    except iam.exceptions.NoSuchEntityException:
        iam.create_instance_profile(InstanceProfileName=PROFILE_NAME,
                                    Tags=[{"Key": "Project", "Value": PROJECT_TAG}])
        iam.add_role_to_instance_profile(InstanceProfileName=PROFILE_NAME, RoleName=ROLE_NAME)
        print(f"  Created instance profile {PROFILE_NAME}")
        print("  Waiting 15s for IAM propagation...")
        time.sleep(15)

    return PROFILE_NAME


def ensure_security_group(ec2):
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    vpc_id = vpcs["Vpcs"][0]["VpcId"]

    existing = ec2.describe_security_groups(Filters=[
        {"Name": "group-name", "Values": [SG_NAME]},
        {"Name": "vpc-id", "Values": [vpc_id]},
    ])
    if existing["SecurityGroups"]:
        sg_id = existing["SecurityGroups"][0]["GroupId"]
        print(f"  SG {sg_id} already exists")
        return sg_id

    resp = ec2.create_security_group(
        GroupName=SG_NAME, Description="Benchmark instances - outbound only",
        VpcId=vpc_id, TagSpecifications=[{
            "ResourceType": "security-group",
            "Tags": [{"Key": "Project", "Value": PROJECT_TAG}]
        }])
    sg_id = resp["GroupId"]
    try:
        sg_info = ec2.describe_security_groups(GroupIds=[sg_id])
        for perm in sg_info["SecurityGroups"][0].get("IpPermissions", []):
            ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[perm])
    except Exception:
        pass
    print(f"  Created SG {sg_id}")
    return sg_id


def build_user_data(account_id, instance_type):
    """User data script: install Docker, pull image, benchmark full render, write results to S3."""
    ecr_uri = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPO}:{ECR_TAG}"
    ecr_registry = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com"
    s3_dest = f"s3://{S3_BUCKET}/{S3_PREFIX}{instance_type.replace('.', '_')}.json"

    # Write everything to files on the host, then run them — avoids ALL quoting issues.
    script = f"""#!/bin/bash
exec > /var/log/benchmark.log 2>&1
set -x
echo "=== Benchmark starting for {instance_type} ==="
BOOT_START=$(date +%s)

dnf install -y docker
systemctl start docker

aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {ecr_registry}

PULL_START=$(date +%s)
docker pull {ecr_uri}
PULL_END=$(date +%s)
PULL_SEC=$(( PULL_END - PULL_START ))
echo "Pull done in ${{PULL_SEC}}s"

"""

    # Write bench scripts as Python heredocs — no substitution needed inside them
    script += r"""
cat > /tmp/bench_full.sh << 'SHEOF'
#!/bin/bash
export PATH="/app/.venv/bin:$PATH"
cd /app
python3 utility.py -r
SHEOF
chmod +x /tmp/bench_full.sh

cat > /tmp/bench_single.py << 'PYEOF'
import sys, time, os
sys.path.insert(0, '/app')
os.chdir('/app')
from web.server import build
from danger.finger_params import RenderQuality
from danger.Scad_Renderer import Scad_Renderer
t0 = time.time()
scad_result = build('tip', {}, RenderQuality.EXTRAMEDIUM)
scad_str = scad_result if isinstance(scad_result, str) else '\n'.join(scad_result)
with open('/tmp/bench_tip.scad', 'w') as f:
    f.write(scad_str)
t1 = time.time()
Scad_Renderer().scad_to_stl('/tmp/bench_tip.scad', '/tmp/bench_tip.stl')
elapsed = time.time() - t1
print('SINGLE_RENDER_SEC=%.1f' % elapsed)
print('TOTAL_SEC=%.1f' % (time.time() - t0))
PYEOF
"""

    script += f"""
RENDER_START=$(date +%s)
docker run --rm \\
  -v /tmp/bench_full.sh:/tmp/bench_full.sh \\
  -e script="/tmp/bench_full.sh" \\
  {ecr_uri}
RENDER_END=$(date +%s)
RENDER_SEC=$(( RENDER_END - RENDER_START ))
echo "Full render done in ${{RENDER_SEC}}s"

SINGLE_START=$(date +%s)
docker run --rm \\
  -v /tmp/bench_single.py:/tmp/bench_single.py:ro \\
  -e script="python3 /tmp/bench_single.py" \\
  {ecr_uri}
SINGLE_END=$(date +%s)
SINGLE_SEC=$(( SINGLE_END - SINGLE_START ))
echo "Single render done in ${{SINGLE_SEC}}s"

MEM_TOTAL=$(free -m | awk '/Mem:/ {{print $2}}')
MEM_PEAK=$(free -m | awk '/Mem:/ {{print $3}}')
TOTAL_END=$(date +%s)
TOTAL_SEC=$(( TOTAL_END - BOOT_START ))

printf '{{"instance_type":"%s","full_render_sec":%d,"single_render_sec":%d,"image_pull_sec":%d,"total_sec":%d,"memory_total_mb":%s,"memory_peak_mb":%s,"timestamp":"%s"}}\\n' \\
  '{instance_type}' "$RENDER_SEC" "$SINGLE_SEC" "$PULL_SEC" "$TOTAL_SEC" "$MEM_TOTAL" "$MEM_PEAK" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \\
  > /tmp/result.json
cat /tmp/result.json

aws s3 cp /tmp/result.json {s3_dest}
echo "Results uploaded to {s3_dest}"

TOKEN=$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -sf -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region {REGION} || echo "Self-terminate failed"
echo "Done."
"""
    return base64.b64encode(script.encode()).decode()


def launch_instances(ec2, ami_id, sg_id, profile_name, instance_types, dry_run=False):
    launched = {}
    account_id = get_account_id(boto3.Session())
    for itype in instance_types:
        print(f"  Launching {itype}...")
        if dry_run:
            launched[itype] = "dry-run"
            continue
        resp = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=itype,
            MinCount=1, MaxCount=1,
            IamInstanceProfile={"Name": profile_name},
            SecurityGroupIds=[sg_id],
            UserData=build_user_data(account_id, itype),
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": f"benchmark-{itype}"},
                    {"Key": "Project", "Value": PROJECT_TAG},
                    {"Key": "Purpose", "Value": "benchmark"},
                ]
            }],
        )
        iid = resp["Instances"][0]["InstanceId"]
        launched[itype] = iid
        print(f"    {iid}")
    return launched


def wait_for_results(s3_client, instance_types, timeout=1800):
    results = {}
    deadline = time.time() + timeout
    pending = set(instance_types)

    while pending and time.time() < deadline:
        for itype in list(pending):
            key = f"{S3_PREFIX}{itype.replace('.', '_')}.json"
            try:
                obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                data = json.loads(obj["Body"].read())
                results[itype] = data
                pending.remove(itype)
                print(f"  Got results for {itype}: full={data['full_render_sec']}s single={data['single_render_sec']}s pull={data['image_pull_sec']}s")
            except s3_client.exceptions.NoSuchKey:
                pass
            except Exception as e:
                print(f"  Error checking {itype}: {e}")

        if pending:
            remaining = int(deadline - time.time())
            print(f"  Waiting for {len(pending)} results... ({remaining}s remaining)")
            time.sleep(30)

    if pending:
        print(f"  TIMEOUT: missing results for {pending}")
    return results


def print_results_table(results):
    print("\n" + "=" * 100)
    print("EC2 BENCHMARK RESULTS — OpenSCAD Render Performance")
    print("=" * 100)
    print(f"{'Type':<14} {'Full(s)':>8} {'Single(s)':>9} {'Pull(s)':>7} {'Mem(MB)':>8} {'$/hr':>7} {'$/render':>9} {'Score':>7}")
    print("-" * 100)

    sorted_types = sorted(results.keys(), key=lambda t: results[t]["full_render_sec"])
    best_score = None
    rows = []

    for itype in sorted_types:
        r = results[itype]
        full_s = r["full_render_sec"]
        single_s = r["single_render_sec"]
        pull_s = r["image_pull_sec"]
        mem = r.get("memory_peak_mb", 0)
        cost_hr = HOURLY_COST.get(itype, 0)
        cost_render = cost_hr * (full_s / 3600)
        # Score: lower is better — cost of one full render cycle
        score = cost_render * 1000

        if best_score is None or score < best_score:
            best_score = score

        rows.append((itype, full_s, single_s, pull_s, mem, cost_hr, cost_render, score))

    for itype, full_s, single_s, pull_s, mem, cost_hr, cost_render, score in rows:
        marker = " <-- BEST" if abs(score - best_score) < 0.001 else ""
        print(f"{itype:<14} {full_s:>8} {single_s:>9} {pull_s:>7} {mem:>8} {cost_hr:>7.4f} {cost_render:>9.5f} {score:>7.3f}{marker}")

    print("-" * 100)
    print("Score = ($/hr × render_time_s / 3600) × 1000  (lower = cheaper per render)")
    print()

    return sorted_types[0] if sorted_types else None


def cleanup(iam, ec2_client, launched):
    print("\nCleanup:")
    for itype, iid in launched.items():
        if iid == "dry-run":
            continue
        try:
            state = ec2_client.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]["State"]["Name"]
            if state not in ("terminated", "shutting-down"):
                ec2_client.terminate_instances(InstanceIds=[iid])
                print(f"  Terminated {iid} ({itype})")
            else:
                print(f"  {iid} ({itype}) already {state}")
        except Exception:
            pass

    s3 = boto3.client("s3", region_name=REGION)
    try:
        objs = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        for obj in objs.get("Contents", []):
            s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
            print(f"  Deleted s3://{S3_BUCKET}/{obj['Key']}")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Benchmark EC2 instances for OpenSCAD rendering")
    parser.add_argument("--dry-run", action="store_true", help="Print user data without launching")
    parser.add_argument("--types", help="Comma-separated instance types")
    parser.add_argument("--timeout", type=int, default=1800, help="Max seconds to wait (default 1800 = 30min)")
    args = parser.parse_args()

    instance_types = args.types.split(",") if args.types else DEFAULT_INSTANCE_TYPES

    session = boto3.Session(region_name=REGION)
    account_id = get_account_id(session)
    iam = session.client("iam")
    ec2 = session.client("ec2")
    s3 = session.client("s3")

    print(f"Account: {account_id}")
    print(f"Testing: {', '.join(instance_types)}")
    print(f"Timeout: {args.timeout}s\n")

    if args.dry_run:
        print("DRY RUN — user data for first type:\n")
        ud = base64.b64decode(build_user_data(account_id, instance_types[0])).decode()
        print(ud)
        return

    print("Setting up infrastructure...")
    profile_name = ensure_iam_role(iam, account_id)
    sg_id = ensure_security_group(ec2)
    ami_id = get_latest_al2023_ami(ec2)
    print(f"  AMI: {ami_id}\n")

    print("Launching instances...")
    launched = launch_instances(ec2, ami_id, sg_id, profile_name, instance_types)
    print(f"\nAll {len(launched)} instances launched. Waiting for results (up to {args.timeout}s)...\n")

    results = wait_for_results(s3, instance_types, timeout=args.timeout)
    best = print_results_table(results)

    if best:
        print(f"RECOMMENDATION: {best} offers the best cost/performance ratio.\n")

    cleanup(iam, ec2, launched)
    print("Done.")


if __name__ == "__main__":
    main()
