"""Lambda handler for S3 read operations — configs, profiles, and bundle.zip.

Fronts the danger-finger S3 bucket via API Gateway HTTP API so AWS credentials
stay server-side.  The container (Tornado) handles writes; this Lambda handles
reads only.
"""

import base64
import json
import os
import re

import boto3
import brotli

S3_BUCKET = os.environ.get("S3_BUCKET", "danger-finger")
PRESIGNED_THRESHOLD = 5 * 1024 * 1024  # 5 MB — use presigned URL above this

s3 = boto3.client("s3")


def handler(event, context):
    path = event.get("rawPath", "") or event.get("path", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if method == "OPTIONS":
        return _cors_response(204, "")

    # GET /configs/{cfghash}
    m = re.match(r"^/configs/([a-fA-F0-9]+)$", path)
    if m:
        return _serve_json("configs/" + m.group(1))

    # GET /profiles/{userhash}
    m = re.match(r"^/profiles/([a-zA-Z0-9.]+)$", path)
    if m:
        return _serve_json("profiles/" + m.group(1))

    # GET /jobs/{job_id}
    m = re.match(r"^/jobs/([a-zA-Z0-9\-]+)$", path)
    if m:
        return _serve_json("jobs/" + m.group(1))

    # GET /render/{cfghash}/status
    m = re.match(r"^/render/([a-fA-F0-9]+)/status$", path)
    if m:
        return _serve_json("render/%s/status" % m.group(1))

    # GET /render/{cfghash}/bundle.zip
    m = re.match(r"^/render/([a-fA-F0-9]+)/bundle\.zip$", path)
    if m:
        return _serve_binary("render/%s/bundle.zip" % m.group(1))

    return _cors_response(404, json.dumps({"error": "Not found"}))


def _get_object(key):
    try:
        resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return resp["Body"].read(), resp.get("ContentLength", 0)
    except s3.exceptions.NoSuchKey:
        return None, 0
    except Exception:
        return None, 0


def _decompress_brotli(data):
    """Decode the project's brotli convention: b'42' prefix means brotli-compressed."""
    if data and data[:2] == b"42":
        return brotli.decompress(data[2:])
    return data


def _serve_json(key):
    data, _ = _get_object(key)
    if data is None:
        return _cors_response(404, json.dumps({"error": "Not found"}))
    body = _decompress_brotli(data)
    return _cors_response(200, body.decode("utf-8"), content_type="application/json")


def _serve_binary(key):
    """Serve binary (ZIP). If >5 MB, redirect to a presigned S3 URL."""
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    except Exception:
        return _cors_response(404, json.dumps({"error": "Not found"}))

    size = head.get("ContentLength", 0)

    if size > PRESIGNED_THRESHOLD:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=300,
        )
        return {
            "statusCode": 302,
            "headers": {
                "Location": url,
                "Access-Control-Allow-Origin": "*",
            },
        }

    data, _ = _get_object(key)
    if data is None:
        return _cors_response(404, json.dumps({"error": "Not found"}))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="%s"' % key.split("/")[-1],
            "Access-Control-Allow-Origin": "*",
        },
        "isBase64Encoded": True,
        "body": base64.b64encode(data).decode("ascii"),
    }


def _cors_response(status, body, content_type="application/json"):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": body,
    }
