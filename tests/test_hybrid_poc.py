"""Static safety checks for the opt-in hybrid Terraform proof of concept."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HYBRID = ROOT / "infra" / "terraform-hybrid"


class TestHybridLayout(unittest.TestCase):
    def test_all_provider_modules_are_present(self):
        for name in ("aws-orchestrator", "gcp-tools", "azure-state", "gcp-knowledge"):
            with self.subTest(module=name):
                self.assertTrue((HYBRID / "modules" / name).is_dir())

    def test_dev_is_disabled_by_default(self):
        variables = (HYBRID / "envs" / "dev" / "variables.tf").read_text()
        self.assertIn('variable "enable_resources"', variables)
        self.assertIn("default     = false", variables)

    def test_poc_does_not_contain_credentials(self):
        contents = "\n".join(path.read_text() for path in HYBRID.rglob("*.tf"))
        self.assertNotIn("access_key", contents)
        self.assertNotIn("secret_key", contents)


if __name__ == "__main__":
    unittest.main()
