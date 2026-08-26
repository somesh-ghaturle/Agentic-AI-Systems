# Static checks on the write boundary.
#
# On this cloud the boundary is not a resource policy, a deny policy, or a flag on an
# application registration. It is the shape of the role graph, and that makes it the
# easiest of the four to break by accident: every way of breaking it is a valid grant that
# applies without error and looks, in isolation, like someone tidying up permissions.
#
#   LOCK 1  modules/tools grants USAGE on each write procedure to the executor role, and
#           to nobody else.
#   LOCK 2  No path through the role graph lets the orchestrator reach the executor's
#           grants. Snowflake roles inherit transitively, so this is a reachability
#           question and not a check on any single grant.
#
# The five failures below are the ones `terraform validate` cannot see. Every one of them
# is syntactically valid, applies cleanly, and shows up in Snowsight looking correct:
#
#   1. `GRANT USAGE ON PROCEDURE <write tool> TO ROLE <orchestrator>`. The direct break.
#   2. A role-graph edge — `snowflake_grant_account_role` with `parent_role_name` — that
#      makes the orchestrator an ancestor of the executor. Two hops away, in a different
#      file from either role, and it hands the orchestrator every write tool at once.
#      modules/orchestration legitimately creates one such edge (TASK_OWNER inherits
#      EXECUTOR), which is why this is a graph walk rather than a blocklist of pairs.
#   3. `execute_as = "CALLER"` on a write procedure. Fails closed rather than open — the
#      write errors instead of succeeding — but a fail-closed write boundary is an outage
#      whose cause is invisible, so it is still a defect.
#   4. Dropping the `SQLROWCOUNT` check from CLAIM_APPROVAL. Two executors then both claim
#      the same approval and the write tool runs twice for one human authorization.
#   5. Granting SNOWFLAKE.CORTEX_USER to the orchestrator. The guarded model wrapper stays
#      exactly where it is, and becomes optional.
#
# This reads the source, not a plan, so it needs no Snowflake account and runs anywhere:
#
#     python3 -m unittest discover -s infra/terraform-snowflake/tests
#
# It is the Snowflake counterpart to the three suites under infra/terraform-*/tests/.

import os
import re
import unittest

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESOURCE_HEADER = re.compile(r'resource\s+"(?P<type>[^"]+)"\s+"(?P<name>[^"]+)"\s*\{')


def strip_comments(text):
    """Remove `#` and `//` line comments, ignoring markers inside double-quoted strings.

    These files explain the boundary at length, and the prose necessarily quotes the very
    strings this file hunts for — modules/tools spends a paragraph on why EXECUTE AS
    CALLER is the wrong answer, and modules/security names the grant that would collapse
    the graph. Matching inside a comment would make the suite fail on its own
    documentation, which teaches people to write around it rather than to read it.

    Heredoc bodies are not string-quoted, so a `#` inside one is treated as a comment.
    Nothing checked here depends on heredoc content surviving intact — the SQL assertions
    below look for tokens that never follow a `#` on the same line.
    """
    out = []
    for line in text.splitlines():
        buf = []
        in_string = False
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                if ch == "\\":
                    buf.append(line[i:i + 2])
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                buf.append(ch)
                i += 1
                continue
            if ch == '"':
                in_string = True
                buf.append(ch)
                i += 1
                continue
            if ch == "#" or (ch == "/" and line[i:i + 2] == "//"):
                break
            buf.append(ch)
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def tf_files(*relative):
    root = os.path.join(TREE, *relative)
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".terraform"]
        for fn in sorted(filenames):
            if fn.endswith(".tf"):
                found.append(os.path.join(dirpath, fn))
    return found


def blocks(path):
    """Yield (type, name, body) for each top-level resource block in a file."""
    with open(path, encoding="utf-8") as fh:
        text = strip_comments(fh.read())
    for match in RESOURCE_HEADER.finditer(text):
        start = match.end()
        depth = 1
        i = start
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        yield match.group("type"), match.group("name"), text[start:i - 1]


def all_blocks(*relative):
    for path in tf_files(*relative):
        for typ, name, body in blocks(path):
            yield path, typ, name, body


def attr(body, key):
    """First value of a simple `key = value` assignment, as written."""
    m = re.search(rf'^\s*{re.escape(key)}\s*=\s*(.+?)\s*$', body, re.M)
    return m.group(1) if m else None


class WriteBoundary(unittest.TestCase):
    # --- LOCK 1 -----------------------------------------------------------

    def test_write_procedures_are_granted_only_to_the_executor(self):
        """USAGE on a write tool goes to var.executor_role and to nothing else.

        modules/tools has exactly one resource granting on write_tools. A second one, or a
        changed role reference on this one, is the direct break.
        """
        offenders = []
        for path, typ, name, body in all_blocks("modules", "tools"):
            if typ != "snowflake_grant_privileges_to_account_role":
                continue
            if "var.write_tools" not in body and "write_signatures" not in body:
                continue
            role = attr(body, "account_role_name")
            if role != "var.executor_role":
                rel = os.path.relpath(path, TREE)
                offenders.append(f"{rel}: {name} grants on write tools to {role}")

        self.assertEqual(
            offenders, [],
            "A write tool is granted to something other than the executor role. That is the "
            "write boundary:\n  " + "\n  ".join(offenders),
        )

    def test_write_tool_grant_to_executor_exists(self):
        """The lock is present at all.

        A boundary asserted only by absence passes trivially once the grant is deleted, and
        a deleted grant is an outage rather than a breach — but it is still not this design.
        """
        found = [
            name for _, typ, name, body in all_blocks("modules", "tools")
            if typ == "snowflake_grant_privileges_to_account_role"
            and attr(body, "account_role_name") == "var.executor_role"
            and "write_signatures" in body
        ]
        self.assertTrue(found, "No resource grants write-tool USAGE to the executor role.")

    # --- LOCK 2 -----------------------------------------------------------

    def test_orchestrator_cannot_reach_the_executor_through_the_role_graph(self):
        """No transitive path from the orchestrator role to the executor role.

        `snowflake_grant_account_role` with `parent_role_name` makes the parent inherit the
        child. modules/orchestration creates one such edge deliberately — TASK_OWNER
        inherits EXECUTOR — so the check has to walk the graph rather than forbid the
        resource. What must never exist is a path that ends at the executor and starts at
        the orchestrator.
        """
        edges = {}
        for _path, typ, _name, body in all_blocks("modules"):
            if typ != "snowflake_grant_account_role":
                continue
            parent = attr(body, "parent_role_name")
            child = attr(body, "role_name")
            if parent is None or child is None:
                continue  # the user_name form grants a role to a user, not to a role
            edges.setdefault(parent, set()).add(child)

        def reaches(start, target, seen=None):
            seen = seen or set()
            for nxt in edges.get(start, ()):
                if nxt in seen:
                    continue
                seen.add(nxt)
                if nxt == target or reaches(nxt, target, seen):
                    return True
            return False

        self.assertFalse(
            reaches("var.orchestrator_role", "var.executor_role"),
            "The orchestrator role reaches the executor role through the role graph. "
            f"Snowflake roles inherit transitively, so this hands the orchestrator every "
            f"write tool at once. Edges: {edges}",
        )

    def test_no_role_is_granted_to_the_orchestrator(self):
        """Nothing is granted *into* the orchestrator role at all.

        Stricter than the reachability check above and deliberately so: the orchestrator is
        a leaf by design. Any inbound edge is a widening whose consequence has to be
        re-derived by hand, and the reachability test only catches the one that reaches the
        executor today.
        """
        inbound = [
            f"{os.path.relpath(path, TREE)}: {name} -> {attr(body, 'role_name')}"
            for path, typ, name, body in all_blocks("modules")
            if typ == "snowflake_grant_account_role"
            and attr(body, "parent_role_name") == "var.orchestrator_role"
        ]
        self.assertEqual(
            inbound, [],
            "A role is granted to the orchestrator, making it inherit that role's privileges:\n  "
            + "\n  ".join(inbound),
        )

    # --- The procedure-level guarantees -----------------------------------

    def test_every_tool_procedure_executes_as_owner(self):
        """EXECUTE AS OWNER on every procedure in tools and approval.

        With OWNER the caller needs only USAGE, so no caller role holds a table privilege
        and the grants above are the complete story. With CALLER the body runs with the
        caller's own privileges and the boundary becomes a claim about every grant made
        anywhere else in the account.
        """
        offenders = []
        for area in ("tools", "approval", "model"):
            for path, typ, name, body in all_blocks("modules", area):
                if not typ.startswith("snowflake_procedure_"):
                    continue
                if attr(body, "execute_as") != '"OWNER"':
                    offenders.append(f"{os.path.relpath(path, TREE)}: {name}")
        self.assertEqual(
            offenders, [],
            "A procedure does not run as OWNER, so its body runs with the caller's "
            "privileges:\n  " + "\n  ".join(offenders),
        )

    def test_claim_procedure_checks_the_affected_row_count(self):
        """CLAIM_APPROVAL keeps its SQLROWCOUNT check.

        That check is the entire concurrency control. Without it two executors racing the
        same approval both believe they won, and one human approval becomes two write-tool
        invocations.
        """
        bodies = [
            body for _, typ, name, body in all_blocks("modules", "approval")
            if typ == "snowflake_procedure_sql" and name == "claim_approval"
        ]
        self.assertEqual(len(bodies), 1, "Expected exactly one claim_approval procedure.")
        self.assertIn(
            "SQLROWCOUNT", bodies[0],
            "CLAIM_APPROVAL no longer checks SQLROWCOUNT. Two executors can then claim the "
            "same approval and the write tool runs twice for one authorization.",
        )

    def test_approve_is_not_granted_to_a_machine_role(self):
        """APPROVE goes to human roles only.

        A machine role that can move a record to APPROVED can approve its own proposal,
        which turns the gate into a formality that still passes every other test here.
        """
        offenders = []
        for path, typ, name, body in all_blocks("modules", "approval"):
            if typ != "snowflake_grant_privileges_to_account_role":
                continue
            if 'procedures["approve"]' not in body:
                continue
            role = attr(body, "account_role_name")
            if role in ("var.orchestrator_role", "var.executor_role"):
                offenders.append(f"{os.path.relpath(path, TREE)}: {name} grants APPROVE to {role}")
        self.assertEqual(
            offenders, [],
            "APPROVE is granted to a machine role:\n  " + "\n  ".join(offenders),
        )

    # --- The guardrail's wiring -------------------------------------------

    def test_orchestrator_is_not_granted_cortex_directly(self):
        """The orchestrator holds the guarded wrapper, not raw Cortex.

        SNOWFLAKE.CORTEX_USER carries the ability to call COMPLETE with no guard. Granting
        it to the orchestrator leaves COMPLETE_GUARDED in place, still looking like a
        control, and makes using it optional.
        """
        offenders = []
        for path, typ, name, body in all_blocks("modules"):
            if typ != "snowflake_grant_database_role":
                continue
            db_role = attr(body, "database_role_name") or ""
            parent = attr(body, "parent_role_name")
            if "CORTEX_USER" in db_role and parent == "var.orchestrator_role":
                offenders.append(f"{os.path.relpath(path, TREE)}: {name}")
        self.assertEqual(
            offenders, [],
            "SNOWFLAKE.CORTEX_USER is granted to the orchestrator, making the guarded "
            "wrapper bypassable:\n  " + "\n  ".join(offenders),
        )

    # --- The container the boundary depends on ----------------------------

    def test_tools_schema_uses_managed_access(self):
        """The TOOLS schema is managed-access.

        Without it, the owner of a procedure may grant on that procedure. The write
        boundary would then be a statement about grants in this repository plus every grant
        any object owner has ever made outside it — and the second half is not observable
        from here. Managed access is what makes the first half sufficient.
        """
        for _path, typ, name, body in all_blocks("modules", "state"):
            if typ == "snowflake_schema" and name == "tools":
                self.assertEqual(
                    attr(body, "with_managed_access"), "true",
                    "The TOOLS schema is not managed-access, so procedure owners can grant "
                    "USAGE on their own procedures and the boundary is unobservable.",
                )
                return
        self.fail("No snowflake_schema.tools found in modules/state.")

    def test_no_future_or_all_privilege_grants_to_caller_roles(self):
        """No blanket grants that would sweep in write procedures added later.

        `future_schemas_in_database`, `all_schemas_in_database` and `all_privileges` each
        turn a specific grant into an open-ended one. A FUTURE PROCEDURES grant to the
        orchestrator covers every write tool added after it, is one line, and is invisible
        in a diff of modules/tools because it does not live there.
        """
        offenders = []
        caller_roles = {"var.orchestrator_role", "var.executor_role", "var.auditor_role"}
        for path, typ, name, body in all_blocks("modules"):
            if typ != "snowflake_grant_privileges_to_account_role":
                continue
            if attr(body, "account_role_name") not in caller_roles:
                continue
            dangers = ("all_privileges", "future_schemas_in_database", "all_schemas_in_database")
            for danger in dangers:
                if re.search(rf"\b{danger}\s*=\s*true", body):
                    rel = os.path.relpath(path, TREE)
                    offenders.append(f"{rel}: {name} sets {danger}")
        self.assertEqual(
            offenders, [],
            "A caller role holds an open-ended grant that will cover objects created "
            "later:\n  " + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
