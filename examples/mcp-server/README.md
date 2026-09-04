# mcp-server — a tool server whose writes still need a human

An MCP-shaped server that advertises a state-changing tool and refuses to run it without a
single-use approval bound to that call's exact arguments.

```bash
python3 examples/mcp-server/server.py --demo
```

```
tools/list advertises both kinds:
  look_up_order    read-only
  refund_order     approval required

calling refund_order with no approval:
  'refund_order' changes state and requires an approval token; request one for these exact arguments first

with an approval granted for a DIFFERENT amount:
  approval does not match this call; it was granted for a different action

with the approval that matches:
  refunded 4000.0 on order 991

reusing the same token:
  approval has already been used
```

## Why this example exists

The repository warns about tool servers without showing a trustworthy one. `GLOSSARY.md`
defines MCP, and `infra/terraform-aws/checklists/pre-apply.md` says to vet a tool server the way
you would a CI plugin. That is the cautionary half. This is the constructive half: the tool list
comes from outside the codebase, and a write still cannot happen without a human approving that
specific action.

That matters more for a tool server than for a local module, because the usual mental model
breaks. When tools are declared in Python, the set of things an agent can do is fixed at review
time. When they arrive over a protocol, the set is whatever the server said this morning — and
the server can add `refund_order` between one call and the next.

## Discovery is not authorization

The write tool is **advertised**, not hidden:

```json
{"name": "refund_order",
 "annotations": {"readOnlyHint": false, "requiresApproval": true}}
```

Hiding it would be a weaker design that looks stronger. A hidden tool is protected by the client
not guessing its name, which is not a boundary — it is missing documentation. The annotation is a
courtesy to a well-behaved client; the refusal in `_call_tool` is what actually holds, and the
tests call the tool directly to prove it.

## The claim is bound to the arguments, not the tool

`fingerprint()` hashes `{"tool": ..., "arguments": ...}` with `sort_keys=True`. An approval for
`refund_order` in the abstract is not a promise a human can meaningfully make; an approval for
*refunding order 991 for $4,000* is. The test that matters here grants an approval for $10 and
calls with $4,000, and expects a refusal.

The token is removed from the arguments before fingerprinting, and before the tool is called.
Fingerprinting the dict that still carried it would let a caller approve one action and execute
another by editing a field afterwards.

## The split is structural, reused from `tool-discovery`

Two registries, each refusing at `register()` to hold a tool of the other access level, so
`MCPServer` has no collection of "all tools" for a call to resolve against. The branch that runs
a tool without claiming an approval can only ever see the read registry. That structure is
`examples/tool-discovery/`'s and is restated here rather than imported — an example that reaches
into a sibling for its core mechanism stops being readable alone, and the dependency graph
between examples is checked and kept shallow on purpose.

**Mutation tested**, twice. Removing the `token is None` check so writes run unguarded turns two
tests red; deleting the access-level refusal in `ToolRegistry.register` turns two different ones
red. Both were run and reverted. A boundary nobody has tried to break is a boundary nobody knows
the strength of.

## What this is not

Not a conformant MCP implementation. It speaks `initialize`, `tools/list`, and `tools/call` over
stdio and ignores notifications, cancellation, progress, resources, prompts, and content-type
negotiation. The subset is chosen to be the smallest thing that can carry the point; a gap in
protocol conformance is a bug report, not a vulnerability. See `SECURITY.md`, which names this
example's claim and its limits.

There is also no transport authentication, no rate limit, and no persistence — approvals live in
a dict and vanish with the process. `examples/hermes-agent/` shows the same claim primitive in a
router, and the three cloud trees in `infra/` show it backed by real storage.

## Running the tests

```bash
python3 examples/mcp-server/server.py --demo
python3 -m unittest tests.test_mcp_server -v          # 19 tests
python3 -m unittest tests.smoke.test_example_smoke -v # runs --demo as a subprocess
```

Nothing to install; Python 3.9 or newer.
