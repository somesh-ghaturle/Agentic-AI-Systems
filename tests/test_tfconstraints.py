"""Tests the provider-constraint checker, and the drift it exists to catch.

    python3 -m unittest tests.test_tfconstraints -v

Standard library only and no `terraform` binary, so this runs in the dependency-free CI job
alongside tests/test_starter_agent.py.

Two things are worth stating about what is tested here. The first is that most of these cases
are written against synthetic HCL in a temp directory rather than against `infra/`. A guard
asserted only against a tree that currently passes tells you nothing — it would keep passing
if the rule stopped being enforced at all. The synthetic cases are the ones that prove the
check *fails* when it should, which is the only property that matters for a guard.

The second is that one test does run against the real `infra/` tree. That is not redundant
with the synthetic cases: it is what catches the regex quietly ceasing to match this
repository's actual HCL — a rule that parses nothing reports no findings and passes, which is
indistinguishable from success unless something asserts the expected constraints are actually
being seen.
"""

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "tfconstraints.py"

_spec = importlib.util.spec_from_file_location("tfconstraints", SCRIPT)
tfconstraints = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tfconstraints)


def write(directory, name, body):
    path = pathlib.Path(directory) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def run(directory):
    """Run the checker as a subprocess. Returns (exit code, combined output)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(directory)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


PINNED = """
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.44"
    }
  }
}
"""


class TestParsing(unittest.TestCase):
    def test_extracts_source_and_constraint(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, "main.tf", PINNED)
            found = list(tfconstraints.constraints(path))
        self.assertEqual([(7, "hashicorp/google", "~> 7.44")], found)

    def test_required_version_is_not_a_provider_constraint(self):
        """The CLI floor must not be mistaken for a provider floor.

        This is the bug the first version of this guard shipped with: a grep for
        `version *= *">="` matched all 29 `required_version = ">= 1.6"` lines, every one of
        them correct. Capping the Terraform CLI to a major buys nothing.
        """
        with tempfile.TemporaryDirectory() as d:
            path = write(d, "main.tf", PINNED)
            found = list(tfconstraints.constraints(path))
        self.assertEqual(["hashicorp/google"], [source for _, source, _ in found])
        self.assertNotIn(">= 1.6", [constraint for _, _, constraint in found])

    def test_tolerates_a_comment_between_source_and_version(self):
        body = """
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"

      # Pinned to a major. See docs/REPO-AUDIT.md task 21.
      version = "~> 7.44"
    }
  }
}
"""
        with tempfile.TemporaryDirectory() as d:
            path = write(d, "main.tf", body)
            found = [(s, c) for _, s, c in tfconstraints.constraints(path)]
        self.assertEqual([("hashicorp/google", "~> 7.44")], found)

    def test_reports_the_line_of_the_constraint(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, "main.tf", PINNED)
            lineno, _, _ = next(iter(tfconstraints.constraints(path)))
        self.assertEqual("      version = \"~> 7.44\"", PINNED.splitlines()[lineno - 1])


class TestFloorRule(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED)
            code, out = run(d)
        self.assertEqual(0, code, out)

    def test_floor_fails(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED.replace("~> 7.44", ">= 7.44"))
            code, out = run(d)
        self.assertEqual(1, code, out)
        self.assertIn("FLOOR", out)
        self.assertIn("hashicorp/google", out)

    def test_required_version_floor_alone_passes(self):
        """A file with only a CLI floor and no providers must not fail."""
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", 'terraform {\n  required_version = ">= 1.6"\n}\n')
            code, out = run(d)
        self.assertEqual(0, code, out)


class TestMismatchRule(unittest.TestCase):
    def test_same_constraint_across_files_passes(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED)
            write(d, "modules/tools/main.tf", PINNED)
            code, out = run(d)
        self.assertEqual(0, code, out)

    def test_partial_bump_fails(self):
        """The exact drift that motivated this rule.

        Dependabot bumped `hashicorp/google` to `~> 7.44` across the roots and modules and
        left one file behind on `~> 6.0`. Both constraints are pins, so the floor rule is
        silent, and both resolve, so `terraform validate` is silent too.
        """
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED)
            write(d, "modules/tools/main.tf", PINNED)
            write(d, "versions.tf", PINNED.replace("~> 7.44", "~> 6.0"))
            code, out = run(d)
        self.assertEqual(1, code, out)
        self.assertIn("MISMATCH", out)
        self.assertIn("versions.tf", out)

    def test_mismatch_names_every_site(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "a.tf", PINNED)
            write(d, "b.tf", PINNED.replace("~> 7.44", "~> 6.0"))
            _, out = run(d)
        self.assertIn("a.tf", out)
        self.assertIn("b.tf", out)
        self.assertIn("~> 6.0", out)
        self.assertIn("~> 7.44", out)

    def test_different_providers_may_differ(self):
        """Two providers on different majors is normal, not drift."""
        other = PINNED.replace("hashicorp/google", "hashicorp/random").replace(
            "~> 7.44", "~> 3.6"
        )
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED)
            write(d, "envs/dev/random.tf", other)
            code, out = run(d)
        self.assertEqual(0, code, out)


class TestSkipsVendoredDirectories(unittest.TestCase):
    def test_dot_terraform_is_ignored(self):
        """`.terraform/` holds downloaded module copies whose constraints are not ours."""
        with tempfile.TemporaryDirectory() as d:
            write(d, "envs/dev/main.tf", PINNED)
            write(d, "envs/dev/.terraform/modules/x/main.tf", PINNED.replace("~> 7.44", ">= 1.0"))
            code, out = run(d)
        self.assertEqual(0, code, out)


class TestRealTree(unittest.TestCase):
    """Guards against the regex silently matching nothing. See the module docstring."""

    def test_infra_passes(self):
        code, out = run(REPO / "infra")
        self.assertEqual(0, code, out)

    def test_infra_constraints_are_actually_being_read(self):
        found = {}
        for path in tfconstraints.tf_files(REPO / "infra"):
            for _, source, constraint in tfconstraints.constraints(path):
                found.setdefault(source, set()).add(constraint)

        # The six providers the four trees declare. If this list needs editing because a
        # provider was added or dropped, that is a real change and should be a real edit.
        self.assertEqual(
            {
                "hashicorp/aws",
                "hashicorp/azuread",
                "hashicorp/azurerm",
                "hashicorp/google",
                "hashicorp/random",
                "snowflakedb/snowflake",
            },
            set(found),
        )
        for source, cs in found.items():
            self.assertEqual(1, len(cs), f"{source} declared {len(cs)} ways: {sorted(cs)}")
            self.assertTrue(
                next(iter(cs)).startswith("~>"), f"{source} does not pin a major: {cs}"
            )


def lock(version):
    return f'''
provider "registry.terraform.io/hashicorp/google" {{
  version     = "{version}"
  constraints = "~> 7.44"
  hashes = [
    "h1:placeholder=",
  ]
}}
'''


class TestRule3LockedVersionsAgreeWithinATree(unittest.TestCase):
    """Staging rehearsing a different provider than prod is what this rule exists to stop."""

    def layout(self, d, versions):
        for tree_env, version in versions.items():
            write(d, f"infra/{tree_env}/main.tf", PINNED)
            write(d, f"infra/{tree_env}/.terraform.lock.hcl", lock(version))
        return pathlib.Path(d) / "infra"

    def test_one_env_ahead_of_the_others_fails(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run(self.layout(d, {
                "terraform-gcp/envs/dev": "7.45.0",
                "terraform-gcp/envs/prod": "7.45.0",
                "terraform-gcp/envs/staging": "7.46.0",
            }))
        self.assertEqual(1, code, out)
        self.assertIn("LOCK     terraform-gcp: hashicorp/google resolved 2 ways", out)
        self.assertIn("envs/staging/.terraform.lock.hcl 7.46.0", out)

    def test_aligned_envs_pass(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run(self.layout(d, {
                "terraform-gcp/envs/dev": "7.46.0",
                "terraform-gcp/envs/staging": "7.46.0",
            }))
        self.assertEqual(0, code, out)

    def test_separate_trees_may_differ(self):
        """The hybrid POC is its own tree and moves on its own schedule."""
        with tempfile.TemporaryDirectory() as d:
            code, out = run(self.layout(d, {
                "terraform-gcp/envs/dev": "7.45.0",
                "terraform-hybrid/envs/dev": "7.46.0",
            }))
        self.assertEqual(0, code, out)

    def test_the_real_tree_has_one_version_per_provider_per_tree(self):
        resolved = {}
        for tree, _, source, version in tfconstraints.locked(REPO / "infra"):
            resolved.setdefault((tree, source), set()).add(version)
        self.assertTrue(resolved, "no lock files found; the rule is guarding nothing")
        for key, versions in resolved.items():
            self.assertEqual(1, len(versions), f"{key} resolved {sorted(versions)}")


if __name__ == "__main__":
    unittest.main()
