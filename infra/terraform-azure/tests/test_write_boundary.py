# Static checks on the write boundary.
#
# The Azure tree draws its write boundary with one attribute:
#
#     app_role_assignment_required = true
#
# ARCHITECTURE.md §2 explains why that single line is load-bearing in a way no single
# line is on the AWS side. Flip it to false and Entra will mint a token for any principal
# in the tenant, while every diagram, output, and role assignment still looks correct.
# Nothing in `terraform validate` notices, and nothing in a plan diff draws attention to
# it — it is a one-word change in a file full of one-word settings.
#
# The obvious guard would be Azure Policy. It cannot be: Azure Policy evaluates resources
# represented in Azure Resource Manager, and Entra app registrations are Microsoft Graph
# objects with no ARM representation and no policy alias. See modules/entra-audit for the
# detective control that covers changes made outside Terraform.
#
# This file covers the other half: changes made *to* Terraform. It reads the source, not
# a plan, so it needs no Azure credentials and runs anywhere.
#
#     python3 -m unittest discover -s infra/terraform-azure/tests

import os
import re
import unittest

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every service principal in this tree fronts a protected resource API — a tool, the
# approval validator, the approval executor, the trace emitter. None of them is a client
# principal, so the rule below is universal rather than a list of exceptions. A new
# service principal that genuinely should admit the whole tenant would need this test
# changed, which is the point: it should take an argument in review, not a silent commit.
REQUIRED = "app_role_assignment_required"

SP_HEADER = re.compile(
    r'resource\s+"azuread_service_principal"\s+"(?P<name>[^"]+)"\s*\{',
)

# Terraform line comments. These files explain the write boundary at length, and that
# prose necessarily quotes the very string this test hunts for — the entra-audit module
# opens by explaining why Azure Policy cannot deny `app_role_assignment_required = false`.
# Matching inside a comment would make the test fail on documentation, which trains people
# to write around it. Stripping comments is not a loophole: HCL does not evaluate them.
COMMENT = re.compile(r"(#|//).*$")


def strip_comments(line):
    return COMMENT.sub("", line)


def strip_comments_preserving_lines(text):
    """Blank out comments while keeping line count and brace structure intact.

    Line-preserving so reported line numbers stay true to the file, and so the brace
    counter in block_body() sees the same structure the file has.
    """
    return "\n".join(strip_comments(line) for line in text.split("\n"))


def tf_files():
    """Every .tf file in the tree, excluding provider caches and example roots."""
    for root, dirs, files in os.walk(TREE):
        dirs[:] = [d for d in dirs if d not in {".terraform", "node_modules", "tests"}]
        for f in sorted(files):
            if f.endswith(".tf"):
                yield os.path.join(root, f)


def block_body(text, open_brace_index):
    """Return the body of the HCL block whose opening brace is at the given index.

    Terraform blocks nest, so a naive search for the next '}' finds the end of the first
    inner block instead of the outer one. This counts depth. Braces inside strings and
    comments would fool it; neither appears inside these particular resources, and a
    miscount would make the test fail loudly rather than pass wrongly.
    """
    depth = 0
    for i in range(open_brace_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : i]
    raise AssertionError("unbalanced braces starting at offset %d" % open_brace_index)


def service_principals():
    """Yield (path, resource_name, body) for every azuread_service_principal block."""
    for path in tf_files():
        with open(path, encoding="utf-8") as fh:
            text = strip_comments_preserving_lines(fh.read())
        for match in SP_HEADER.finditer(text):
            body = block_body(text, match.end() - 1)
            yield path, match.group("name"), body


class TestWriteBoundary(unittest.TestCase):
    def setUp(self):
        self.principals = list(service_principals())

    def test_tree_has_service_principals(self):
        # If the walk breaks, every other test in this file passes vacuously. This is the
        # canary: four principals exist today across tools, approval, and observability.
        self.assertGreaterEqual(
            len(self.principals),
            4,
            "expected at least 4 azuread_service_principal blocks; found %d. Either the "
            "tree changed or the file walk is broken — check the latter first, because a "
            "broken walk makes the rest of this file pass while checking nothing."
            % len(self.principals),
        )

    def test_every_service_principal_requires_role_assignment(self):
        missing = []
        for path, name, body in self.principals:
            assignment = re.search(
                REQUIRED + r"\s*=\s*(?P<value>\S+)",
                body,
            )
            rel = os.path.relpath(path, TREE)
            if assignment is None:
                missing.append("%s: %s — attribute absent" % (rel, name))
            elif assignment.group("value") != "true":
                missing.append(
                    "%s: %s — set to %s" % (rel, name, assignment.group("value"))
                )

        self.assertEqual(
            [],
            missing,
            "Service principals without %s = true:\n  %s\n\n"
            "This is the write boundary. Without it Entra issues a token for these APIs "
            "to any principal in the tenant, and the orchestrator can invoke write tools "
            "directly. See ARCHITECTURE.md §2." % (REQUIRED, "\n  ".join(missing)),
        )

    def test_attribute_is_never_set_false_anywhere(self):
        # Belt and braces. Catches the attribute being set false in a place the block
        # parser does not reach — a locals map, a dynamic block, a module input default.
        offenders = []
        pattern = re.compile(REQUIRED + r"\s*=\s*false")
        for path in tf_files():
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if pattern.search(strip_comments(line)):
                        offenders.append(
                            "%s:%d" % (os.path.relpath(path, TREE), lineno)
                        )

        self.assertEqual(
            [],
            offenders,
            "%s is set to false at:\n  %s" % (REQUIRED, "\n  ".join(offenders)),
        )


if __name__ == "__main__":
    unittest.main()
