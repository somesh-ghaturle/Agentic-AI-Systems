"""Tests the offline Terraform cost estimator.

    python3 -m unittest tests.test_terraform_cost_estimate -v

The script is intentionally offline and deterministic: it only evaluates the Terraform config it
is given, so it can run in CI without credentials or provider access.
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "terraform_cost_estimate.py"


def write(directory, name, body):
    path = pathlib.Path(directory) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def run(directory, threshold=500.0, json_output=False):
    command = [sys.executable, str(SCRIPT), str(directory), "--threshold", str(threshold)]
    if json_output:
        command.append("--json")
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


class TestTerraformCostEstimate(unittest.TestCase):
    def test_counts_resources_and_estimates_cost(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "main.tf", """
            resource "aws_lambda_function" "one" {}
            resource "azurerm_storage_account" "sa" {}
            resource "google_cloudfunctions2_function" "fn" {}
            resource "snowflake_warehouse" "wh" {}
            """)
            code, out = run(d)
        self.assertEqual(0, code, out)
        self.assertIn("Estimated monthly cost", out)
        self.assertIn("aws_lambda_function", out)
        self.assertIn("snowflake_warehouse", out)
        self.assertIn("USD", out)

    def test_threshold_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "main.tf", """
            resource "snowflake_warehouse" "wh" {}
            resource "snowflake_warehouse" "wh2" {}
            """)
            code, out = run(d, threshold=0)
        self.assertEqual(1, code, out)
        self.assertIn("threshold", out.lower())

    def test_missing_path_exits_with_error(self):
        code, out = run(pathlib.Path("/definitely-not-here"), threshold=0)
        self.assertEqual(2, code, out)
        self.assertIn("path not found", out.lower())

    def test_real_tree_smoke_test(self):
        code, out = run(REPO / "infra")
        self.assertEqual(0, code, out)
        self.assertIn("Estimated monthly cost", out)


if __name__ == "__main__":
    unittest.main()
