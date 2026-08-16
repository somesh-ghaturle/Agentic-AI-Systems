# Static checks on the write boundary.
#
# The GCP tree draws its write boundary twice, and this file guards both halves plus the
# three ways each one fails silently.
#
#   LOCK 1  modules/tools grants `roles/run.invoker` on each write tool's Cloud Run
#           service to the approval executor, and to nobody else.
#   LOCK 2  modules/orchestration attaches an IAM Deny policy denying the orchestrator
#           the invoke permission on those same services.
#
# Neither is checkable by `terraform validate`. Every mistake below is a valid string in a
# valid attribute, applies without error, appears in the console looking correct, and
# denies nothing:
#
#   1. `roles/cloudfunctions.invoker` instead of `roles/run.invoker`. A gen2 function is a
#      Cloud Run service underneath and has no invoker binding of its own. The wrong role
#      grants nothing — which is silent in the safe direction for read tools and silent in
#      the dangerous direction for write tools, because the write tool is then invokable by
#      anyone holding run.invoker from some other grant.
#   2. `serviceAccount:` in a deny policy's principals. Deny policies take `principal://`
#      form. The allow-policy form is accepted and matches nothing.
#   3. Handing the orchestrator a write tool's invoker binding, or a write tool's URL.
#
# This reads the source, not a plan, so it needs no GCP credentials and runs anywhere:
#
#     python3 -m unittest discover -s infra/terraform-gcp/tests
#
# It is the GCP counterpart to infra/terraform-azure/tests/test_write_boundary.py, which
# guards a different single point of failure — `app_role_assignment_required`. The AWS tree
# needs no equivalent: there, the boundary is a Lambda resource policy, and getting it
# wrong is a plan-time error rather than a quiet one.

import os
import re
import unittest

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESOURCE_HEADER = re.compile(
    r'resource\s+"(?P<type>[^"]+)"\s+"(?P<name>[^"]+)"\s*\{',
)


def strip_comments(line):
    """Remove a Terraform line comment, ignoring comment markers inside strings.

    These files explain the write boundary at length, and that prose necessarily quotes
    the very strings this file hunts for — modules/tools/main.tf opens by explaining why
    `roles/cloudfunctions.invoker` is the dangerous wrong answer. Matching inside a comment
    would make the test fail on its own documentation, which trains people to write around
    it. Stripping is not a loophole: HCL does not evaluate comments.

    The scan is character-by-character rather than a regex because HCL accepts `//` as a
    comment marker and the deny policy's principals are `principal://...` URIs. A
    `(#|//).*$` regex truncates that line to `"principal:`, and the resulting failure
    reports "no principal:// entry in denied_principals" — pointing straight at the deny
    policy while describing the wrong problem.

    Heredoc bodies are not string-quoted, so a `#` inside one is still treated as a
    comment. Nothing parsed here depends on heredoc content surviving intact.
    """
    out = []
    in_string = False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_string:
            if ch == "\\":
                out.append(line[i : i + 2])
                i += 2
                continue
            if ch == '"':
                in_string = False
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "#" or (ch == "/" and line[i + 1 : i + 2] == "/"):
            break
        out.append(ch)
        i += 1
    return "".join(out)


def strip_comments_preserving_lines(text):
    """Blank out comments while keeping line count and brace structure intact.

    Line-preserving so reported line numbers stay true to the file, and so the brace
    counter in block_body() sees the same structure the file has.
    """
    return "\n".join(strip_comments(line) for line in text.split("\n"))


def tf_files(subdir=None):
    """Every .tf file in the tree, excluding provider caches and this directory."""
    root_dir = TREE if subdir is None else os.path.join(TREE, subdir)
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in {".terraform", "node_modules", "tests"}]
        for f in sorted(files):
            if f.endswith(".tf"):
                yield os.path.join(root, f)


def block_body(text, open_brace_index):
    """Return the body of the HCL block whose opening brace is at the given index.

    Terraform blocks nest, so a naive search for the next '}' finds the end of the first
    inner block instead of the outer one. This counts depth. Braces inside strings would
    fool it; none appear inside these particular resources, and a miscount would make the
    test fail loudly rather than pass wrongly.
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


def resources(resource_type=None, subdir=None):
    """Yield (path, type, name, body) for every resource block in the tree."""
    for path in tf_files(subdir):
        with open(path, encoding="utf-8") as fh:
            text = strip_comments_preserving_lines(fh.read())
        for match in RESOURCE_HEADER.finditer(text):
            if resource_type is not None and match.group("type") != resource_type:
                continue
            yield path, match.group("type"), match.group("name"), block_body(
                text, match.end() - 1
            )


def rel(path):
    return os.path.relpath(path, TREE)


class TestLockOneInvokerBindings(unittest.TestCase):
    """modules/tools: write tools are invokable by the approval executor and nobody else."""

    def setUp(self):
        self.bindings = list(resources("google_cloud_run_service_iam_member"))

    def test_tree_has_invoker_bindings(self):
        # If the file walk breaks, every other test here passes vacuously. This is the
        # canary: read tools, write tools, the validator, the executor's approvers, and the
        # trace emitter all carry one of these today.
        self.assertGreaterEqual(
            len(self.bindings),
            4,
            f"expected at least 4 google_cloud_run_service_iam_member blocks; "
            f"found {len(self.bindings)}. "
            "Either the tree changed or the file walk is broken — check the latter first, "
            "because a broken walk makes the rest of this file pass while checking "
            "nothing.",
        )

    def test_write_tool_bindings_name_the_approval_executor(self):
        """Any binding iterating write tools must grant to the executor.

        Keyed off `local.write_tools` rather than off the resource name, so renaming the
        resource does not slip past the check.
        """
        checked = 0
        wrong = []

        for path, _type, name, body in self.bindings:
            if "local.write_tools" not in body:
                continue
            checked += 1

            member = re.search(r"member\s*=\s*(?P<value>\S+)", body)
            if member is None:
                wrong.append(f"{rel(path)}: {name} — no member attribute")
            elif member.group("value") != "var.approval_executor_member":
                wrong.append(
                    "{}: {} — grants to {}".format(rel(path), name, member.group("value"))
                )

        self.assertEqual(
            [],
            wrong,
            "Write tool invoker bindings that do not name the approval executor:\n  {}\n\n"
            "This is lock 1. The executor is the only principal permitted to invoke a "
            "write tool; anything else here means the model can execute irreversible "
            "actions without passing the gate.".format("\n  ".join(wrong)),
        )

        self.assertEqual(
            1,
            checked,
            f"expected exactly 1 invoker binding over local.write_tools; found {checked}. "
            "More than one means a second principal is being granted invoke on write tools "
            "somewhere — read it before changing this number.",
        )

    def test_orchestrator_never_appears_in_a_write_tool_binding(self):
        offenders = [
            f"{rel(path)}: {name}"
            for path, _type, name, body in self.bindings
            if "local.write_tools" in body and "var.orchestrator_member" in body
        ]

        listed = "\n  ".join(offenders)
        self.assertEqual(
            [],
            offenders,
            f"The orchestrator is named in a write tool invoker binding at:\n  {listed}\n\n"
            "The orchestrator proposes writes. It does not execute them — that inversion "
            "is the single most important safety property in the system.",
        )


class TestInvokerRoleIsCloudRun(unittest.TestCase):
    """The gen2 function trap: cloudfunctions.invoker looks right and controls nothing."""

    def test_cloudfunctions_invoker_is_never_granted(self):
        offenders = []
        pattern = re.compile(r"roles/cloudfunctions\.invoker")

        for path in tf_files():
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if pattern.search(strip_comments(line)):
                        offenders.append(f"{rel(path)}:{lineno}")

        listed = "\n  ".join(offenders)
        self.assertEqual(
            [],
            offenders,
            f"roles/cloudfunctions.invoker is granted at:\n  {listed}\n\n"
            "Every function in this tree is Cloud Functions gen2, which is a Cloud Run "
            "service underneath. This role appears in the console, applies without error, "
            "and does not control HTTP invocation. Use "
            "google_cloud_run_service_iam_member with roles/run.invoker.",
        )

    def test_no_gen2_function_iam_resources(self):
        """The same mistake in resource form rather than role form."""
        offenders = [
            f"{rel(path)}: {name}"
            for path, rtype, name, _body in resources()
            if rtype.startswith("google_cloudfunctions2_function_iam")
        ]

        listed = "\n  ".join(offenders)
        self.assertEqual(
            [],
            offenders,
            f"Function-level IAM resources found at:\n  {listed}\n\n"
            "These manage the function resource's own policy, which is not what gates "
            "invocation for gen2. Bind the underlying Cloud Run service instead.",
        )


class TestLockTwoDenyPolicy(unittest.TestCase):
    """modules/orchestration: the deny policy, and the two ways it applies but does nothing."""

    def setUp(self):
        self.policies = list(resources("google_iam_deny_policy"))

    def test_the_deny_policy_exists(self):
        self.assertEqual(
            1,
            len(self.policies),
            f"expected exactly 1 google_iam_deny_policy; found {len(self.policies)}. "
            "This is lock 2 — the independent denial that survives somebody later granting "
            "the orchestrator a broad run.invoker at project level.",
        )

    def test_denied_principals_use_principal_uri_form(self):
        wrong = []
        for path, _type, name, body in self.policies:
            block = re.search(
                r"denied_principals\s*=\s*\[(?P<items>[^\]]*)\]", body, re.S
            )
            if block is None:
                wrong.append(f"{rel(path)}: {name} — no denied_principals")
                continue

            items = block.group("items")
            if "principal://" not in items:
                wrong.append(
                    f"{rel(path)}: {name} — no principal:// entry in denied_principals"
                )
            if re.search(r'"serviceAccount:', items):
                wrong.append(
                    f'{rel(path)}: {name} — uses "serviceAccount:" form'
                )

        self.assertEqual(
            [],
            wrong,
            "Deny policy principals in the wrong form:\n  {}\n\n"
            "Deny policies take principal:// URIs, unlike every other IAM resource in this "
            "tree, which takes serviceAccount:. The allow-policy form is accepted at apply "
            "time and matches nothing — the policy exists, looks like a control, and denies "
            "nobody.".format("\n  ".join(wrong)),
        )

    def test_denied_permissions_cover_cloud_run_invoke(self):
        wrong = []
        for path, _type, name, body in self.policies:
            if "denied_permissions" not in body:
                wrong.append(f"{rel(path)}: {name} — no denied_permissions")

        self.assertEqual([], wrong, "\n  ".join(wrong))

        # The default lives in variables.tf rather than in the resource body, so check it
        # there. `run.googleapis.com/routes.invoke` is what roles/run.invoker actually
        # confers; without it the deny rule covers the gen1 path only and the real one
        # stays open.
        variables = os.path.join(TREE, "modules", "orchestration", "variables.tf")
        with open(variables, encoding="utf-8") as fh:
            text = strip_comments_preserving_lines(fh.read())

        self.assertIn(
            "run.googleapis.com/routes.invoke",
            text,
            "denied_invoke_permissions no longer defaults to include "
            "run.googleapis.com/routes.invoke. That is the permission behind "
            "roles/run.invoker, and it is the one doing the work — a deny rule without it "
            "applies cleanly and leaves the invoke path open.",
        )

    def test_deny_condition_is_scoped_to_write_tools(self):
        for path, _type, name, body in self.policies:
            self.assertIn(
                "var.write_tool_service_names",
                body,
                f"{rel(path)}: {name} — the denial condition does not reference "
                "write_tool_service_names. An unscoped denial would also cut the "
                "orchestrator off from read tools, the validator, and the trace emitter, "
                "which fails loudly; a condition built from something else may fail "
                "quietly.",
            )


class TestWriteToolUrlsHaveOneConsumer(unittest.TestCase):
    """The shape layer: the orchestrator is never handed a write tool's address."""

    def test_env_roots_pass_only_read_tool_urls_to_orchestration(self):
        offenders = []
        for env in ("dev", "prod"):
            path = os.path.join(TREE, "envs", env, "main.tf")
            with open(path, encoding="utf-8") as fh:
                text = strip_comments_preserving_lines(fh.read())

            match = re.search(r'module\s+"orchestration"\s*\{', text)
            self.assertIsNotNone(
                match, f"{rel(path)} has no orchestration module block"
            )
            body = block_body(text, match.end() - 1)

            for forbidden in (
                "module.tools.write_tool_urls",
                "module.tools.tool_urls_by_name",
            ):
                if forbidden in body:
                    offenders.append(f"{rel(path)}: passes {forbidden}")

        self.assertEqual(
            [],
            offenders,
            "The orchestration module is handed write tool addresses at:\n  {}\n\n"
            "A URL is not a secret and this is not the security control — IAM is. It is "
            "the shape layer, and it exists so that reaching a write tool has to be "
            "deliberate rather than incidental.".format("\n  ".join(offenders)),
        )

    def test_write_tool_urls_go_to_the_approval_module_only(self):
        for env in ("dev", "prod"):
            path = os.path.join(TREE, "envs", env, "main.tf")
            with open(path, encoding="utf-8") as fh:
                text = strip_comments_preserving_lines(fh.read())

            total = text.count("module.tools.write_tool_urls")
            match = re.search(r'module\s+"approval"\s*\{', text)
            self.assertIsNotNone(match, f"{rel(path)} has no approval module block")
            in_approval = block_body(text, match.end() - 1).count(
                "module.tools.write_tool_urls"
            )

            self.assertEqual(
                total,
                in_approval,
                f"{rel(path)} references module.tools.write_tool_urls {total} times but "
                f"only {in_approval} are inside the approval module. The executor is the "
                "only thing that should know a write tool's address.",
            )


if __name__ == "__main__":
    unittest.main()
