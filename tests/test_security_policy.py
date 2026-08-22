"""Pins SECURITY.md to the tree it describes, so its scope list cannot quietly go stale.

    python3 -m unittest tests.test_security_policy -v

A security policy is a promise to someone outside the project about what is worth reporting.
Unlike prose elsewhere in the repository, it decays silently: nothing breaks when an example is
added and nobody classifies it, and the person who finds out is a researcher who wasted an
afternoon on something the maintainers considered out of scope all along.

Both failures these tests check for were live when they were written.

`checkpoint-agent` and `e2e-agent` appeared in neither list. checkpoint-agent had just been
added; e2e-agent had been unclassified for longer, and is the more interesting of the two, since
it advertises "security gating" while implementing no approval step.

And the out-of-scope paragraph claimed each of those examples "says in its own README that it
makes no security claim" — which was true of none of them. `starter-agent` and
`langchain-agent` did not mention security, production, or claims anywhere at all.

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLICY = ROOT / "SECURITY.md"
EXAMPLES = ROOT / "examples"

# The disclaimer sentence SECURITY.md promises is in each out-of-scope README.
DISCLAIMER = "makes no security claim"

# `identity` is deliberately absent from the AWS tree, which keeps its identity policy in
# modules/orchestration instead — see terraform-aws's ARCHITECTURE.md, "Identity policy |
# modules/orchestration". So these four are the set every tree must have; anything else the
# policy names only has to resolve somewhere.
UNIVERSAL_MODULES = ("orchestration", "tools", "approval", "security")
TREES = ("terraform-aws", "terraform-azure", "terraform-gcp")


def named_modules():
    """Module names SECURITY.md actually lists, read from the page rather than hardcoded.

    Hardcoding the list would mean a typo introduced into SECURITY.md — or a module renamed
    only there — sails past the very test meant to catch it.
    """
    # The list wraps across lines, so collapse the section before matching: reading it
    # line by line silently drops whichever names fall on the first line.
    text = " ".join(section("## In scope").split())
    cut = text.find(" modules")
    if cut != -1:
        bullet = text.rfind("- **", 0, cut)
        names = re.findall(r"`([a-z][a-z0-9-]*)`", text[bullet:cut])
        if names:
            return tuple(names)
    raise AssertionError("found no backticked module names in SECURITY.md's in-scope section")


def example_dirs():
    """Every example directory, which is the set the policy has to account for."""
    return sorted(
        p.name
        for p in EXAMPLES.iterdir()
        if p.is_dir() and not p.name.startswith((".", "__"))
    )


def section(heading):
    """The body of one `## ` section of SECURITY.md."""
    body, capturing = [], False
    for line in POLICY.read_text().splitlines():
        if line.startswith("## "):
            capturing = line.strip() == heading
            continue
        if capturing:
            body.append(line)
    return "\n".join(body)


class TestEveryExampleIsClassified(unittest.TestCase):
    """An example the policy does not mention has no stated scope, which is the failure."""

    def test_every_example_is_named_in_the_policy(self):
        policy = POLICY.read_text()
        unclassified = [name for name in example_dirs() if name not in policy]
        self.assertEqual(
            unclassified,
            [],
            "examples/ directories missing from SECURITY.md — add each to the in-scope or "
            f"out-of-scope list: {unclassified}",
        )

    def test_the_two_boundary_examples_are_in_scope(self):
        in_scope = section("## In scope")
        for name in ("hermes-agent", "graph-agent"):
            self.assertIn(name, in_scope)


class TestOutOfScopeExamplesDisclaim(unittest.TestCase):
    """The policy says these READMEs disclaim; this is that sentence being true."""

    def test_each_out_of_scope_example_readme_disclaims(self):
        out_of_scope = section("## Out of scope")
        named = [name for name in example_dirs() if name in out_of_scope]
        self.assertTrue(named, "parsed no example names out of the out-of-scope section")

        missing = []
        for name in named:
            readme = EXAMPLES / name / "README.md"
            if DISCLAIMER not in readme.read_text().lower():
                missing.append(name)

        self.assertEqual(
            missing,
            [],
            f"SECURITY.md says these READMEs disclaim, but {DISCLAIMER!r} is absent: {missing}",
        )


class TestNamedModulesResolve(unittest.TestCase):
    """A policy pointing at a module that does not exist points nowhere."""

    def test_universal_modules_exist_in_all_three_trees(self):
        missing = [
            f"{tree}/modules/{module}"
            for tree in TREES
            for module in UNIVERSAL_MODULES
            if not (ROOT / "infra" / tree / "modules" / module).is_dir()
        ]
        self.assertEqual(missing, [], f"modules named by SECURITY.md are absent: {missing}")

    def test_every_named_module_resolves_in_at_least_one_tree(self):
        for module in named_modules():
            trees = [t for t in TREES if (ROOT / "infra" / t / "modules" / module).is_dir()]
            self.assertTrue(trees, f"SECURITY.md names {module!r}, which exists in no tree")


if __name__ == "__main__":
    unittest.main()
