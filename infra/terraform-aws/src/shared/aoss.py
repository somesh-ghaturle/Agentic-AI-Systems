# OpenSearch Serverless client — SigV4 over urllib, no third-party dependencies.
#
# The zips these handlers build are plain directories. Adding opensearch-py means a build
# step with pip, a platform-specific wheel cache, and a package large enough to lose the
# console editor. botocore ships in the Lambda runtime and already knows how to sign, so
# the whole client is one signed POST.

import json
import os
import urllib.error
import urllib.request

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

SERVICE = "aoss"

_endpoint_cache = {}


def resolve_endpoint(collection_name, region=None):
    """Looks the collection endpoint up by name.

    The endpoint contains the generated collection ID, so it cannot be constructed from
    known values and cannot be passed in as a Terraform variable without a dependency
    cycle (tools -> knowledge -> orchestration -> tools). Resolving it here at cold start
    keeps the module graph acyclic. Requires aoss:BatchGetCollection.
    """
    if collection_name in _endpoint_cache:
        return _endpoint_cache[collection_name]

    client = boto3.client("opensearchserverless", region_name=region or _region())
    response = client.batch_get_collection(names=[collection_name])
    collections = response.get("collectionDetails") or []
    if not collections:
        raise RuntimeError(
            f"No OpenSearch Serverless collection named {collection_name!r}. "
            "Check KNOWLEDGE_COLLECTION against the knowledge module's name_prefix."
        )

    endpoint = collections[0]["collectionEndpoint"]
    _endpoint_cache[collection_name] = endpoint
    return endpoint


def search(endpoint, index, body, region=None, timeout=10):
    """Runs a query and returns the parsed response body."""
    return _request(
        "POST", f"{endpoint.rstrip('/')}/{index}/_search", body, region, timeout
    )


def _request(method, url, body, region, timeout):
    region = region or _region()
    payload = json.dumps(body).encode("utf-8")

    request = AWSRequest(
        method=method,
        url=url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    credentials = boto3.Session().get_credentials()
    if credentials is None:
        raise RuntimeError("No AWS credentials available to sign the request.")
    SigV4Auth(credentials.get_frozen_credentials(), SERVICE, region).add_auth(request)

    urllib_request = urllib.request.Request(
        url, data=payload, headers=dict(request.headers), method=method
    )
    try:
        with urllib.request.urlopen(urllib_request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"OpenSearch returned {exc.code}: {detail}") from exc


def _region():
    return os.environ.get("AWS_REGION") or os.environ.get(
        "AWS_DEFAULT_REGION", "us-east-1"
    )
