#!/usr/bin/env python3
"""Audit AWS account for danger-finger resources. Reports all active resources, costs, and anomalies."""
import boto3
import json

REGION = "us-east-1"

def main():
    session = boto3.Session(region_name=REGION)
    account = session.client("sts").get_caller_identity()
    print(f"Account: {account['Account']}  Region: {REGION}\n")

    # EC2
    ec2 = session.client("ec2")
    instances = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}])
    running = [i for r in instances["Reservations"] for i in r["Instances"]]
    print(f"EC2 instances: {len(running)}")
    for i in running:
        name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
        print(f"  {i['InstanceId']} ({i['InstanceType']}) {name} — {i['State']['Name']}")

    eips = ec2.describe_addresses()["Addresses"]
    unassoc = [e for e in eips if "InstanceId" not in e]
    print(f"Elastic IPs: {len(eips)} ({len(unassoc)} unassociated)")

    # VPCs
    vpcs = ec2.describe_vpcs()["Vpcs"]
    non_default = [v for v in vpcs if not v["IsDefault"]]
    print(f"Non-default VPCs: {len(non_default)}")

    # ECS
    ecs = session.client("ecs")
    clusters = ecs.list_clusters()["clusterArns"]
    print(f"ECS clusters: {len(clusters)}")

    # ALB
    elbv2 = session.client("elbv2")
    albs = elbv2.describe_load_balancers()["LoadBalancers"]
    print(f"Load balancers: {len(albs)}")

    # S3
    s3 = session.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    print(f"S3 buckets: {[b['Name'] for b in buckets]}")

    # ECR
    ecr = session.client("ecr")
    repos = ecr.describe_repositories()["repositories"]
    print(f"ECR repos: {len(repos)}")
    for r in repos:
        images = ecr.list_images(repositoryName=r["repositoryName"])["imageIds"]
        print(f"  {r['repositoryUri']}: {len(images)} images")

    # Lambda
    lam = session.client("lambda")
    functions = lam.list_functions()["Functions"]
    print(f"Lambda functions: {len(functions)}")
    for f in functions:
        print(f"  {f['FunctionName']} ({f['Runtime']}) {f['MemorySize']}MB")

    # API Gateway
    apigw = session.client("apigatewayv2")
    apis = apigw.get_apis()["Items"]
    print(f"API Gateways: {len(apis)}")
    for a in apis:
        print(f"  {a['Name']} ({a['ApiEndpoint']})")

    # IAM
    iam = session.client("iam")
    users = iam.list_users()["Users"]
    roles = iam.list_roles()["Roles"]
    custom_roles = [r for r in roles if not r["Path"].startswith("/aws-service-role/")]
    print(f"IAM users: {len(users)}, custom roles: {len(custom_roles)}")
    for u in users:
        keys = iam.list_access_keys(UserName=u["UserName"])["AccessKeyMetadata"]
        active = sum(1 for k in keys if k["Status"] == "Active")
        print(f"  {u['UserName']}: {active} active keys")

    # CloudFormation
    cf = session.client("cloudformation")
    stacks = cf.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE", "DELETE_FAILED"])
    active_stacks = [s["StackName"] for s in stacks["StackSummaries"]]
    print(f"CF stacks: {active_stacks}")

    # Route53
    r53 = session.client("route53")
    zones = r53.list_hosted_zones()["HostedZones"]
    print(f"Route53 zones: {len(zones)}")

    print("\nAudit complete.")


if __name__ == "__main__":
    main()
