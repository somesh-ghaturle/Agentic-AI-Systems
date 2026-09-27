# Static checks on the write boundary.
#
# The Azure tree draws its write boundary with one attribute:
#
#     app_role_assignment_required = true
#
# ARCHITECTURE.md section 2 explains why that single line is load-bearing in a way no single
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


def strip_comments(line):
    """Remove a Terraform line comment, ignoring comment markers inside strings.

    Character-by-character rather than a `(#|//).*$` regex, matching the AWS, GCP and
    Snowflake suites. The regex is wrong specifically here: this tree's identity surface is
    built from `api://` and `https://` values — modules/tools/main.tf:82 and :252,
    modules/observability/outputs.tf:41 — and cutting at `//` truncates them mid-value.
    In modules/tools/outputs.tf that also swallowed a closing brace, leaving text whose
    brace balance differed from the file's; block_body() counts braces on this output, so
    it would have read the wrong body or raised on a well-formed file. Ten files in this
    tree carry `//` or `#` inside a quoted string.

    Heredoc bodies are not string-quoted, so a `#` inside one is still treated as a
    comment. Nothing asserted here depends on heredoc content surviving intact.
    """
    out = []
    in_string = False
    escaped = False
    index = 0
    while index < len(line):
        char = line[index]
        if escaped:
            out.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            out.append(char)
            escaped = True
            index += 1
            continue
        if char == '"':
            in_string = not in_string
            out.append(char)
            index += 1
            continue
        if not in_string:
            if char == "#":
                break
            if char == "/" and index + 1 < len(line) and line[index + 1] == "/":
                break
        out.append(char)
        index += 1
    return "".join(out)


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
    raise AssertionError(f"unbalanced braces starting at offset {open_brace_index}")


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
            f"expected at least 4 azuread_service_principal blocks; "
            f"found {len(self.principals)}. Either the tree changed or the file walk is "
            "broken — check the latter first, because a broken walk makes the rest of "
            "this file pass while checking nothing.",
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
                missing.append(f"{rel}: {name} — attribute absent")
            elif assignment.group("value") != "true":
                missing.append(
                    "{}: {} — set to {}".format(rel, name, assignment.group("value"))
                )

        self.assertEqual(
            [],
            missing,
            "Service principals without {} = true:\n  {}\n\n"
            "This is the write boundary. Without it Entra issues a token for these APIs "
            "to any principal in the tenant, and the orchestrator can invoke write tools "
            "directly. See ARCHITECTURE.md section 2.".format(REQUIRED, "\n  ".join(missing)),
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
                        offenders.append(f"{os.path.relpath(path, TREE)}:{lineno}")

        self.assertEqual(
            [],
            offenders,
            "{} is set to false at:\n  {}".format(REQUIRED, "\n  ".join(offenders)),
        )


class TestWhoHoldsTheWriteRole(unittest.TestCase):
    """What `app_role_assignment_required = true` actually enforces (task 87).

    That attribute makes Entra require *an* assignment. Which identity holds the assignment
    is the lock's content, and it was untested. A mutation audit assigned the write-tool
    role to the orchestrator, widened the orchestrator's assignment to every tool, and
    turned off Easy Auth, and this suite stayed green each time. With the orchestrator
    holding the write role, the required-assignment check passes and admits it.
    """

    TOOLS = os.path.join(TREE, "modules", "tools", "main.tf")

    def setUp(self):
        with open(self.TOOLS, encoding="utf-8") as fh:
            self.text = strip_comments_preserving_lines(fh.read())

    def _resources(self, rtype):
        for m in re.finditer(r'resource\s+"' + rtype + r'"\s+"(?P<name>\w+)"\s*\{', self.text):
            yield m.group("name"), block_body(self.text, m.end() - 1)

    def _attr(self, body, key):
        m = re.search(r"^\s*" + key + r"\s*=\s*(?P<v>.+)$", body, re.M)
        return m.group("v").strip() if m else None

    def test_write_tools_are_assigned_to_the_executor_only(self):
        assignments = list(self._resources("azuread_app_role_assignment"))
        self.assertGreaterEqual(len(assignments), 2, "role assignments not found; walk broken?")
        for name, body in assignments:
            principal = self._attr(body, "principal_object_id")
            for_each = self._attr(body, "for_each")
            if principal == "var.approval_executor_principal_id":
                self.assertEqual(for_each, "local.write_tools", name)
            elif principal == "var.orchestrator_principal_id":
                self.assertEqual(for_each, "local.read_tools",
                                 f"{name} assigns the orchestrator a role over {for_each}")
            else:
                self.fail(f"{name}: unexpected principal {principal}")
        executor_id = "var.approval_executor_principal_id"
        executors = [n for n, b in assignments
                     if self._attr(b, "principal_object_id") == executor_id]
        self.assertEqual(len(executors), 1, "the executor's write-tool assignment is missing")

    def test_the_tool_filters_split_on_access(self):
        self.assertRegex(self.text, r'read_tools\s*=\s*\{[^}]*if v\.access == "read"\s*\}')
        self.assertRegex(self.text, r'write_tools\s*=\s*\{[^}]*if v\.access == "write"\s*\}')

    def test_every_tool_app_rejects_unauthenticated_callers(self):
        """Easy Auth is the Azure form of a Lambda resource policy, and it was untested."""
        found = 0
        for m in re.finditer(r"auth_settings_v2\s*\{", self.text):
            body = block_body(self.text, m.end() - 1)
            found += 1
            self.assertEqual(self._attr(body, "auth_enabled"), "true")
            self.assertEqual(self._attr(body, "require_authentication"), "true")
            self.assertEqual(self._attr(body, "unauthenticated_action"), '"Return401"')
        self.assertGreaterEqual(found, 1, "no auth_settings_v2 block in modules/tools")


class TestTheReaderItself(unittest.TestCase):
    """The reader is a claim like any other, and it was the one nothing checked.

    Every assertion above is only as good as the text it reads. Three sibling trees scan
    comments character-by-character and say in their docstrings that a `(#|//).*$` regex is
    the wrong tool here; this tree used that regex until the brace test below caught it
    truncating `api://` URIs mid-value.
    """

    def test_a_url_inside_a_string_survives(self):
        line = '  identifier_uris = ["api://${var.name_prefix}-tool-${each.key}"]'
        self.assertEqual(strip_comments(line), line)

    def test_a_real_comment_is_still_removed(self):
        self.assertEqual(strip_comments("a = 1  # trailing").rstrip(), "a = 1")
        self.assertEqual(strip_comments("b = 2  // trailing").rstrip(), "b = 2")

    def test_stripping_never_changes_brace_balance(self):
        # The failure mode that matters: block_body() counts braces on stripped text, so a
        # stripper that eats a closing brace makes it read the wrong body or raise on a file
        # that is perfectly well-formed.
        for path in tf_files():
            with open(path, encoding="utf-8") as handle:
                raw = handle.read()
            stripped = strip_comments_preserving_lines(raw)
            self.assertEqual(
                raw.count("{") - raw.count("}"),
                stripped.count("{") - stripped.count("}"),
                f"{os.path.relpath(path, TREE)}: comment stripping changed the brace balance",
            )


if __name__ == "__main__":
    unittest.main()
