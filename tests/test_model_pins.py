"""Pins every model identifier in `infra/` to an allowlist, so the trees cannot drift apart.

    python3 -m unittest tests.test_model_pins -v

Task 46 found `claude-opus-4-5@20251101` pinned in the GCP tree while the handler beside it sent
`thinking={"type": "adaptive"}` — a call shape that model does not support. The tree could not
have run. Nothing caught it because nothing in the repository knew what the other three trees
pinned, so there was no "these disagree" for anything to notice.

This is that check. It is deliberately dumb: it reads model-shaped tokens out of the files and
asserts each one appears on a list maintained below. It cannot tell you a model is current, only
that a pin changed without the list changing with it — which is exactly the moment task 46's
defect entered, and the moment a human should look.

**No network.** Every other suite here is safe to gate a merge on because it does not depend on
anything outside the checkout, and a test that asked a provider's catalog whether a model still
existed would trade that away for an answer this test does not need. The cost is that the list
below goes stale on its own schedule. That is the honest shape of the problem rather than a
solution to it: the list is a record of a human decision, and it expires the way decisions do.

The four trees do not agree, and are not supposed to. Azure runs `gpt-4o` on purpose — see
DECISION-LOGS/0002-azure-openai-vs-claude.md, which chose Azure OpenAI for its attachable content
filter and named the condition under which that should be revisited. Snowflake runs whatever
`SNOWFLAKE.CORTEX.COMPLETE` offers, on Snowflake's schedule, not ours. Divergence is a finding
only when it is unexplained, so each entry below carries its reason.

No dependencies; runs in the fast `examples` CI job.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
INFRA = ROOT / "infra"

# Matches a vendor model identifier in any of the shapes the trees use: a Bedrock ID carrying its
# `anthropic.` prefix, a bare Vertex/Cortex ID, a dated Vertex snapshot (`...@20251101`), and the
# OpenAI family Azure deploys. Deliberately broad — a stale identifier in a variable description
# is the same drift as one in a default, and task 46's was in both.
MODEL_TOKEN = re.compile(
    r"(?:anthropic\.)?claude-[a-z0-9]+(?:-[a-z0-9]+)*(?:@[0-9]+)?"
    r"|gpt-[a-z0-9]+(?:[.-][a-z0-9]+)*"
)

# Every identifier each tree is allowed to contain, and why that tree holds what it does.
ALLOWED = {
    # Bedrock IDs carry the vendor prefix. The bare form also appears here, as the `model_version`
    # written onto a trace record — a different field from the model ID, and not a pin.
    "terraform-aws": {"anthropic.claude-opus-5", "claude-opus-5"},
    # Vertex addresses current-generation models by the bare first-party ID. Set by task 46.
    "terraform-gcp": {"claude-opus-5"},
    # Cortex serves the models Snowflake chooses to offer. Behind the other Claude trees, and not
    # ours to bump: verify against Snowflake's current catalog before changing this.
    "terraform-snowflake": {"claude-sonnet-4-5"},
    # Deliberate, per ADR 0002. Not drift.
    "terraform-azure": {"gpt-4o"},
    # A rego fixture asserting the Azure guardrail wiring, so it mirrors the Azure tree.
    "policies": {"gpt-4o"},
    # No model pin of its own; it composes the trees above.
    "terraform-hybrid": set(),
}

SKIP_DIRS = {".terraform", "__pycache__", ".git"}

# Files where a leading `#` starts a comment. Full-line comments are dropped before scanning,
# because a comment is the one place a model identifier legitimately appears without being a
# pin — the Snowflake tree names `claude-opus-5` precisely to record that it deliberately does
# not use it, and flagging that would train the reader to edit the allowlist to silence prose.
#
# Terraform `description` strings are NOT comments and stay in scope. That distinction is the
# useful one: a description is contract surface a user reads, and task 46's stale identifier was
# sitting in one. Markdown is scanned whole, since `#` there is a heading.
COMMENT_SYNTAX = {".tf", ".tfvars", ".py", ".hcl", ".example", ".rego"}


def _scannable(path):
    """File text with full-line comments removed, where the format has them."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    if path.suffix not in COMMENT_SYNTAX:
        return text
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _tokens(tree):
    """Every model identifier in one tree, mapped to the files it appears in."""
    found = {}
    root = INFRA / tree
    for path in root.rglob("*"):
        if not path.is_file() or any(p in SKIP_DIRS for p in path.parts):
            continue
        text = _scannable(path)
        if text is None:
            continue
        for match in MODEL_TOKEN.findall(text):
            found.setdefault(match, set()).add(str(path.relative_to(ROOT)))
    return found


class TestModelPins(unittest.TestCase):
    def test_every_tree_is_covered(self):
        """A new tree under infra/ must be classified, not silently unchecked."""
        trees = {p.name for p in INFRA.iterdir() if p.is_dir() and p.name not in SKIP_DIRS}
        self.assertEqual(
            trees,
            set(ALLOWED),
            "infra/ gained or lost a tree; add it to ALLOWED with the reason it pins what it does",
        )

    def test_no_pin_outside_its_allowlist(self):
        for tree, allowed in ALLOWED.items():
            with self.subTest(tree=tree):
                for token, files in sorted(_tokens(tree).items()):
                    self.assertIn(
                        token,
                        allowed,
                        f"{tree} pins {token!r} (in {', '.join(sorted(files))}) which is not on "
                        f"its allowlist {sorted(allowed)}. If this is an intended bump, update "
                        f"ALLOWED in this file and confirm the handler's call shape still matches "
                        f"the model — that pairing is what task 46 got wrong.",
                    )

    def test_allowlist_has_no_dead_entries(self):
        """An entry nothing uses is a pin that was removed without the list following."""
        for tree, allowed in ALLOWED.items():
            with self.subTest(tree=tree):
                present = set(_tokens(tree))
                self.assertEqual(
                    allowed - present,
                    set(),
                    f"{tree}'s allowlist names identifiers the tree no longer contains; "
                    f"remove them so the list keeps describing the tree",
                )


if __name__ == "__main__":
    unittest.main()
