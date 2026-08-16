# Static checks on the write boundary.
#
# ---------------------------------------------------------------------------
# Why this file exists, when the AWS boundary was supposed to be self-enforcing
# ---------------------------------------------------------------------------
#
# The claim made elsewhere in this repo is that the AWS tree needs no write-boundary test,
# because the boundary is a Lambda resource policy and getting it wrong is a plan-time
# error. That is true of the resource policy and only of the resource policy:
# `aws_lambda_permission.write_tool_from_approval` carries a precondition that fails the
# plan when a write tool is declared with no approval gate in front of it.
#
# It is not true of the other half. For a caller in the SAME ACCOUNT, Lambda grants
# invocation if the identity policy allows it OR the resource policy does. The orchestrator's
# identity policy is built from `var.tool_function_arns`, and nothing checks what is in that
# list. Widen it to every tool — `module.tools.tool_arns_by_name` instead of
# `read_tool_arns` is a one-word edit that reads as a simplification — and the state machine
# can invoke the write tools directly. The resource policy does not stop it, no precondition
# fires, `terraform validate` passes, and the plan shows an IAM statement gaining an ARN.
#
# That is the failure this file guards, along with the smaller ways the same boundary is
# undone quietly:
#
#   1. A write tool ARN reaching the orchestrator's identity policy.
#   2. The write tools' resource policy naming `states.amazonaws.com` — the orchestrator's
#      principal — instead of the approval executor.
#   3. `read_tool_arns` losing its `access == "read"` filter, which turns the output the
#      env roots trust into every tool.
#
# This reads the source, not a plan, so it needs no AWS credentials and runs anywhere:
#
#     python3 -m unittest discover -s infra/terraform-aws/tests
#
# It is the AWS counterpart to infra/terraform-azure/tests/test_write_boundary.py and
# infra/terraform-gcp/tests/test_write_boundary.py, each of which guards the single point of
# failure its own provider presents.

import os
import re
import unittest

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESOURCE_HEADER = re.compile(r'resource\s+"(?P<type>[^"]+)"\s+"(?P<name>[^"]+)"\s*\{')


def strip_comments(line):
    """Remove a Terraform line comment, ignoring comment markers inside strings.

    These files explain the write boundary at length, and that prose necessarily quotes the
    very strings this file hunts for — modules/tools/main.tf opens by explaining that write
    tools must never be invoked by the orchestrator, naming both principals. Matching inside
    a comment would make the test fail on its own documentation, which trains people to write
    around it. Stripping is not a loophole: HCL does not evaluate comments.

    Character-by-character rather than a regex because ARNs contain `//` in neither form but
    policy documents do contain `#` inside strings, and a `(#|//).*$` regex would truncate
    them mid-value and report a missing attribute while describing the wrong problem.
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
    return "\n".join(strip_comments(line) for line in text.split("\n"))


def tf_files(*subdirs):
    for subdir in subdirs:
        root = os.path.join(TREE, subdir)
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".tf"):
                    yield os.path.join(dirpath, filename)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return strip_comments_preserving_lines(handle.read())


def block_body(text, open_brace_index):
    """Returns the balanced body of a block starting at an opening brace."""
    depth = 0
    for index in range(open_brace_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : index]
    return ""


def resource_bodies(resource_type, *subdirs):
    """Yields (path, name, body) for every resource of a type."""
    for path in tf_files(*subdirs):
        text = read(path)
        for match in RESOURCE_HEADER.finditer(text):
            if match.group("type") != resource_type:
                continue
            body = block_body(text, match.end() - 1)
            yield path, match.group("name"), body


class TestOrchestratorCannotReachWriteTools(unittest.TestCase):
    """The identity-policy half of the boundary, which has no precondition behind it."""

    def test_env_roots_never_pass_write_tool_arns_to_the_orchestrator(self):
        forbidden = ("write_tool_arns", "tool_arns_by_name")

        for path in tf_files("envs"):
            text = read(path)
            index = text.find("tool_function_arns")
            if index == -1:
                continue

            # The value is a concat(...) spanning several lines; take from the attribute to
            # the end of its balanced parentheses.
            start = text.find("(", index)
            self.assertNotEqual(start, -1, f"{path}: tool_function_arns has no expression")
            depth = 0
            end = start
            for position in range(start, len(text)):
                if text[position] == "(":
                    depth += 1
                elif text[position] == ")":
                    depth -= 1
                    if depth == 0:
                        end = position
                        break
            expression = text[index:end]

            for name in forbidden:
                self.assertNotIn(
                    name,
                    expression,
                    f"{path}: tool_function_arns includes {name!r}. The orchestrator's "
                    "identity policy would then allow lambda:InvokeFunction on write "
                    "tools, and for a same-account caller that is sufficient on its own — "
                    "the resource policy does not have to agree. Pass read_tool_arns.",
                )

    def test_orchestrator_policy_has_no_wildcard_lambda_invoke(self):
        """A wildcard resource would reach the write tools without naming them."""
        for path in tf_files("modules/orchestration"):
            text = read(path)
            for match in re.finditer(r'actions\s*=\s*\["lambda:InvokeFunction"\]', text):
                window = text[match.end() : match.end() + 400]
                resources = re.search(r"resources\s*=\s*(.+)", window)
                self.assertIsNotNone(
                    resources, f"{path}: lambda:InvokeFunction with no resources attribute"
                )
                self.assertNotIn(
                    '"*"',
                    resources.group(1),
                    f"{path}: lambda:InvokeFunction on a wildcard resource reaches every "
                    "tool, including the write tools.",
                )


class TestWriteToolResourcePolicy(unittest.TestCase):
    """The resource-policy half — the one with a precondition, checked anyway."""

    def _permission(self, name):
        found = [
            (path, body)
            for path, resource_name, body in resource_bodies(
                "aws_lambda_permission", "modules"
            )
            if resource_name == name
        ]
        self.assertEqual(
            len(found), 1, f"expected exactly one aws_lambda_permission.{name}"
        )
        return found[0]

    def test_write_tools_admit_the_approval_executor_and_not_the_orchestrator(self):
        path, body = self._permission("write_tool_from_approval")

        self.assertIn(
            "approval_executor_arn",
            body,
            f"{path}: the write tools' resource policy must name the approval executor.",
        )
        self.assertNotIn(
            "states.amazonaws.com",
            body,
            f"{path}: states.amazonaws.com is the orchestrator's principal. Naming it here "
            "hands the state machine the write path directly.",
        )
        self.assertNotIn(
            "orchestrator_state_machine_arn",
            body,
            f"{path}: the orchestrator's ARN must not appear on a write tool's permission.",
        )

    def test_write_permission_iterates_write_tools_only(self):
        _, body = self._permission("write_tool_from_approval")
        self.assertIn("local.write_tools", body)

    def test_read_permission_iterates_read_tools_only(self):
        """for_each over every tool would grant the orchestrator the write tools too."""
        path, body = self._permission("read_tool_from_orchestrator")
        self.assertIn("local.read_tools", body)
        self.assertNotIn("var.tools", body, f"{path}: read permission must not span all tools")

    def test_write_permission_keeps_its_approval_gate_precondition(self):
        """The one plan-time guard in the tree. Removing it is silent."""
        _, body = self._permission("write_tool_from_approval")
        self.assertIn("precondition", body)
        self.assertIn("approval_executor_arn != null", body)

    def test_permissions_are_account_scoped(self):
        """Without source_account, a confused-deputy path opens across accounts."""
        for name in ("read_tool_from_orchestrator", "write_tool_from_approval"):
            _, body = self._permission(name)
            self.assertIn("source_account", body, f"{name} is missing source_account")


class TestToolOutputsStayFiltered(unittest.TestCase):
    """The env roots trust these outputs. An unfiltered one quietly widens the boundary."""

    def _output_value(self, name):
        path = os.path.join(TREE, "modules", "tools", "outputs.tf")
        text = read(path)
        match = re.search(rf'output\s+"{re.escape(name)}"\s*\{{', text)
        self.assertIsNotNone(match, f"output {name!r} not found in {path}")
        return block_body(text, match.end() - 1)

    def test_read_tool_arns_filters_on_read_access(self):
        body = self._output_value("read_tool_arns")
        self.assertIn('access == "read"', body)

    def test_write_tool_arns_filters_on_write_access(self):
        body = self._output_value("write_tool_arns")
        self.assertIn('access == "write"', body)

    def test_read_and_write_outputs_are_not_the_same_expression(self):
        self.assertNotEqual(
            self._output_value("read_tool_arns").strip(),
            self._output_value("write_tool_arns").strip(),
        )


class TestAccessClassificationIsEnforced(unittest.TestCase):
    def test_tool_access_is_constrained_to_read_or_write(self):
        """An unrecognised access value would fall out of both locals and be unreachable —
        or worse, land in a future `!= "write"` filter as a read tool."""
        found = False
        for path in tf_files("modules/tools"):
            text = read(path)
            if 'contains(["read", "write"]' in text:
                found = True
        self.assertTrue(
            found,
            "modules/tools must constrain tool access to read or write. Without it a typo "
            "in a tool's access classification silently skips the split.",
        )


if __name__ == "__main__":
    unittest.main()
