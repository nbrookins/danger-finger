import json
import os
import time
import urllib.error
import urllib.request

import boto3


EC2_URL = os.environ["EC2_URL"].rstrip("/")
INSTANCE_ID = os.environ["INSTANCE_ID"]
PROJECT_NAME = os.environ.get("PROJECT_NAME", "danger-finger")
METRIC_NAME = os.environ.get("METRIC_NAME", "AppHealthFailed")
METRIC_NS = os.environ.get("METRIC_NS", "DangerFinger/Monitoring")

cloudwatch = boto3.client("cloudwatch")
ssm = boto3.client("ssm")


def _put_metric(value):
    cloudwatch.put_metric_data(
        Namespace=METRIC_NS,
        MetricData=[
            {
                "MetricName": METRIC_NAME,
                "Timestamp": time.time(),
                "Value": value,
                "Unit": "Count",
            }
        ],
    )


def _probe():
    url = f"{EC2_URL}/api/parts"
    with urllib.request.urlopen(url, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Health check returned HTTP {resp.status}")
        data = json.loads(resp.read().decode("utf-8"))
        if "parts" not in data:
            raise RuntimeError("Health check response missing 'parts'")
        return {"status": resp.status, "parts": len(data["parts"])}


def _attempt_restart():
    restart_cmd = (
        f"docker restart {PROJECT_NAME} || "
        f"docker start {PROJECT_NAME} || "
        f"echo RESTART_FAILED"
    )
    resp = ssm.send_command(
        InstanceIds=[INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [restart_cmd]},
    )
    return resp["Command"]["CommandId"]


def handler(event, context):
    try:
        result = _probe()
        _put_metric(0)
        return {"status": "healthy", "probe": result}
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
        first_error = str(exc)

    try:
        time.sleep(2)
        result = _probe()
        _put_metric(0)
        return {"status": "healthy_after_retry", "probe": result, "first_error": first_error}
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
        second_error = str(exc)

    _put_metric(1)
    try:
        command_id = _attempt_restart()
    except Exception as restart_exc:
        command_id = None
        second_error = f"{second_error}; restart failed: {restart_exc}"

    return {
        "status": "unhealthy",
        "first_error": first_error,
        "second_error": second_error,
        "restart_command_id": command_id,
    }
