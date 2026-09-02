#!/usr/bin/env python3
"""Estimate rough monthly spend from Terraform resources without cloud credentials.

    python3 .github/scripts/terraform_cost_estimate.py infra --threshold 500

This is intentionally a budget guard, not a billing quote. It scans Terraform configuration for
resource blocks and applies conservative rule-of-thumb pricing to common resource classes. That
keeps the check offline and deterministic, which matches this repository's CI constraint: every
workflow must run without cloud credentials.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections.abc import Iterable

RESOURCE_PRICE = {
    "aws_lambda_function": 0.25,
    "aws_dynamodb_table": 0.6,
    "aws_s3_bucket": 0.35,
    "aws_opensearchserverless_collection": 15.0,
    "azurerm_function_app": 7.5,
    "azurerm_linux_function_app": 7.5,
    "azurerm_storage_account": 2.5,
    "azurerm_cosmosdb_account": 12.0,
    "azurerm_cognitive_account": 20.0,
    "google_cloudfunctions_function": 2.5,
    "google_cloudfunctions2_function": 2.5,
    "google_storage_bucket": 0.5,
    "google_firestore_database": 1.0,
    "snowflake_warehouse": 25.0,
    "snowflake_table": 0.1,
}

RESOURCE_RE = re.compile(r'^\s*resource\s+"(?P<type>[^"]+)"\s+"[^"]+"\s*\{', re.MULTILINE)


def iter_tf_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in sorted(root.rglob("*.tf")):
        if ".terraform" in path.parts:
            continue
        yield path


def count_resources(root: pathlib.Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in iter_tf_files(root):
        text = path.read_text(encoding="utf-8")
        for match in RESOURCE_RE.finditer(text):
            resource_type = match.group("type")
            counts[resource_type] = counts.get(resource_type, 0) + 1
    return dict(sorted(counts.items()))


def estimate_monthly_cost(root: pathlib.Path) -> tuple[float, dict[str, int]]:
    counts = count_resources(root)
    total = 0.0
    for resource_type, count in counts.items():
        unit_cost = RESOURCE_PRICE.get(resource_type, 0.0)
        total += count * unit_cost
    return round(total, 2), counts


def classify(total: float) -> str:
    if total < 25:
        return "low"
    if total < 150:
        return "medium"
    if total < 500:
        return "high"
    return "critical"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimate rough monthly spend from Terraform resources without cloud creds.",
    )
    parser.add_argument("path", type=pathlib.Path, help="Terraform directory or file tree to scan")
    parser.add_argument(
        "--threshold",
        type=float,
        default=500.0,
        help="Exit non-zero if the estimate exceeds this threshold (default: 500.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human summary",
    )
    args = parser.parse_args(argv)

    root = args.path
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    try:
        total, counts = estimate_monthly_cost(root)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    status = classify(total)
    payload = {
        "estimated_monthly_usd": total,
        "status": status,
        "resource_counts": counts,
        "threshold_usd": args.threshold,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Estimated monthly cost: ${total:,.2f} USD ({status})")
        if counts:
            print("Resource counts:")
            for resource_type, count in counts.items():
                print(f"  - {resource_type}: {count}")
        else:
            print("No Terraform resource blocks found.")

    if total > args.threshold:
        print(
            f"warning: estimate exceeds threshold (${args.threshold:,.2f} USD)",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
