# second-path

A write boundary that is correct, a test suite that passes, and a write that happens anyway.

```bash
python3 boundary.py                                   # the demonstration
python3 -m unittest tests.test_second_path -v         # from the repository root
```

No dependencies, no model, no key.

## The idea

Every other boundary example here shows a control working. This one shows a control that works
and does not help, because the effect it guards is reachable by a route that never reaches it.

The gate in [`boundary.py`](boundary.py) is not weak. It refuses a write with no approval claim,
refuses a claim that does not match the exact arguments, and binds the claim to a digest so
approving `restart_service` in the abstract is impossible. Six tests cover it. All six pass.

Then `Orchestrator` — a component that is supposed to be a read-only caller — is constructed
with the full tool table instead of the read-only one, and calls the write tool directly:

```text
3. The one-word edit -- READ_TOOLS becomes TOOLS

   restart_service ALLOWED  (restarted billing)
   effects: ['restarted billing']
   The gate was never consulted. It did not fail -- it was not on the path.
   reachable writes: ['restart_service']  <- the check that catches it
```

The gate did not fail open. It was not asked.

## Where this comes from

Not invented. It is a small copy of something this repository found in its own AWS tree, and
the comment atop [`infra/terraform-aws/tests/`](../../infra/terraform-aws/) records it. The
claim had been that the AWS boundary needed no test, because it is a Lambda resource policy and
getting it wrong is a plan-time error:

> That is true of the resource policy and only of the resource policy. […] For a caller in the
> SAME ACCOUNT, Lambda grants invocation if the identity policy allows it **or** the resource
> policy does.

Two independent grants; the precondition governs one. The orchestrator's identity policy is
built from a variable and nothing checked what went into it, so substituting
`tool_arns_by_name` for `read_tool_arns` opens the boundary while `terraform validate` still
passes and no precondition fires.

`READ_TOOLS` → `TOOLS` here is that edit, in a form you can run.

## Why the gate suite cannot tell you

`TestTheGateIsNotEnough` asserts the point rather than describing it. It opens the boundary,
then runs the entire gate suite programmatically and asserts it still passes:

| Configuration | gate suite | `reachable_writes()` |
|---|---|---|
| As designed | passes | `[]` |
| One-word edit | **passes** | `['restart_service']` |

A green gate suite is not evidence the boundary holds. Only a check that asks *what can this
component reach* separates the two rows, and that is a different question from *is the gate
correct* — which is why a system can have a thorough answer to the second and none to the first.

## The check

```python
def reachable_writes(orchestrator):
    return sorted(n for n, t in orchestrator.reachable.items() if t.access == "write")
```

Eleven words of logic, and it is the only thing in the example that distinguishes a boundary
that holds from one that does not. The AWS suite does the same thing against Terraform source
rather than a plan, so it needs no credentials and runs anywhere — a boundary test that only
runs where secrets exist is a boundary test that does not run.

## Tests

16 tests in [`tests/test_second_path.py`](../../tests/test_second_path.py), in the `tests/`
directory with every other example's, because the `examples` CI job discovers that directory.

**Mutation tested.** Four deliberate breaks, all caught:

| Mutation | Result |
|---|---|
| Drop the fingerprint comparison | 2 failures |
| `READ_TOOLS` loses its `access == "read"` filter | 4 failures |
| `Orchestrator` defaults to `TOOLS` | 3 failures — and **the gate suite alone still passes** |
| Drop the `claim is None` branch | 2 failures |

The third row is the example restated as a test result: the same mutation that opens the
boundary leaves the control's own suite green.

The fourth found a real gap. Deleting the `claim is None` branch does not change whether the
call is refused — `None` is not equal to the digest, so the next check catches it — and the
first version of the suite passed with the branch removed. What changes is the *reason* given:
an operator is told their approval did not match when they never sent one. `Refused` exists to
carry which control refused and why, so the tests now assert the message, not just the
exception.

## What is simplified

One component, one write tool, and reachability that is a dict rather than an IAM policy. A
real system has many callers and the question becomes a graph reachability problem — which is
the same question, and worse, because the second path is usually two hops away rather than one.

The gate has no human in it; approval is a digest supplied by the caller. See
[hermes-agent](../hermes-agent/README.md) for the approval flow with a human in it, and
[mcp-server](../mcp-server/README.md) for the same digest binding across a protocol boundary.

## Related

- [ENVIRONMENT-ENGINEERING.md §2](../../docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) — the chapter this example exists for
- [infra/terraform-aws/](../../infra/terraform-aws/) — the real instance, in Terraform
- [tool-discovery](../tool-discovery/README.md) — two registries rather than a filter, which is the *other* way this boundary is lost
- [approval-gate-fuzzing](../approval-gate-fuzzing/README.md) — attacking the gate rather than routing around it

## Security

This example demonstrates a failure deliberately: the `Orchestrator(TOOLS)` path is *supposed*
to execute a write with no approval, and its tests assert that it does. Nothing here is a
control to rely on, and the write "effect" appends to a list. A route from the read-only
orchestrator to a write tool in the **default** configuration would be a real bug in the
example and is in scope; the one in the wide configuration is the subject.
