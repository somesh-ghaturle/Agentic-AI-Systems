# Security policy

## Reporting

Use GitHub's [private vulnerability reporting](https://github.com/somesh-ghaturle/Agentic-AI-Systems/security/advisories/new).
It opens an advisory only the maintainers can read.

Please don't open a public issue for a boundary bypass. The configurations here are meant to be
copied, so a public report is a working recipe against every copy already out there. For
anything else — a broken link, a stale pin, an example that no longer runs — a public issue is
the right place.

A useful report names the file and line, the path by which the boundary is reached, and ideally
the one-line mutation that demonstrates it. The suites under `infra/*/tests/` are written in
that shape and are a good model.

## What counts as a vulnerability here

Nothing in this repository is a running service. There's no deployment to compromise and no
data in it. What there is, is a claim — made three times, in three clouds:

> A state-changing action cannot reach production without a human approving that specific
> action.

The valuable report is that the claim is false: some configuration grants more than it appears
to, the approval step can be bypassed, or a control the docs call load-bearing is decorative.

The harm isn't to this checkout. It's that a pattern which looks correct and isn't gets copied
into real infrastructure, where it becomes a real vulnerability with someone else's name on the
incident.

## In scope

- **The write boundary in all three Terraform trees** — mainly the `orchestration`, `tools`,
  `approval`, `identity`, and `security` modules and the wiring in `envs/*`. Any route to a
  write tool without a valid, unexpired, single-use approval claim; any policy that grants
  invocation more widely than the tree's `ARCHITECTURE.md` claims; any control named as
  load-bearing that doesn't constrain anything.
- **The two boundary examples**, `examples/hermes-agent/` and `examples/graph-agent/`. Both
  exist to demonstrate the read/write split, so a routing path that reaches a write handler
  without approval counts even though neither touches a cloud.
- **This repository's supply chain** — the workflows and scripts under `.github/`, and the
  pinned dependencies.

## Out of scope

The minimal reference examples — `starter-agent`, `langchain-agent`, `rag-faiss`,
`rag-langchain`, `ray-orchestrator`, `context-compaction`, `harness-agent`, `trace-eval`. They
read local files, call models, and print. Each says in its own README that it makes no security
claim, and that they'd be inadequate as production services is documented rather than
accidental.

Two other things that aren't reports, though both are welcome as ordinary issues: raw scanner
output with no argument for why the pattern is wrong, and hardening the docs already name as
deliberately absent. Azure's boundary resting on a single lock is the example — argue the
compensating controls are insufficient and that's in scope; report the absence and it's already
written down.

Vulnerabilities in Terraform, the cloud providers, or third-party libraries belong upstream. If
a version *pinned here* is affected, that's worth telling us.

## What to expect

This is maintained in spare time, so no response timeline is promised — one that isn't met is
worse than none. What you'll get is an acknowledgement, an assessment showing the reasoning
rather than just a verdict, and if it holds up, a fix plus a regression test that fails against
the unfixed version. Credit in the advisory unless you'd rather not have it.

## Supported versions

`main` only. There are no releases and no backports.
