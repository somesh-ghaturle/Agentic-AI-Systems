# tool-discovery

Tools loaded from a directory at runtime, instead of hardcoded in a module — and the read/write
split kept a structural property of the loader rather than a filter over one list.

```bash
python3 discover.py
```

No dependencies, no model, no key.

## The idea

Every other tool-owning example in this repository — [hermes-agent](../hermes-agent/README.md),
[graph-agent](../graph-agent/README.md) — declares its tools in Python, at the top of a module,
written by the same person who wrote the router. That does not scale to a system where tools
arrive by being dropped in: a plugin directory, an installed package, an MCP server's tool
list. Once tools are discovered rather than declared, the read/write split — the property
[BUILDING-BLOCKS.md §2](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md#2--tool-layer-and-api-contracts)
calls the one that actually stops a model from acting unsupervised — has to survive being
discovered too.

`discover.py` scans `tools/`, imports each file, and reads a small contract off it:

| Attribute | Meaning |
| --- | --- |
| `NAME` | The tool's name |
| `ACCESS` | `"read"` or `"write"` — nothing else is accepted |
| `DESCRIPTION` | One line, for a human or a router deciding whether to call it |
| `run(arguments)` | The callable itself |

Three tools ship with the example: `get_weather` and `list_orders` (`read`), and
`restart_service` (`write`).

## Why two registries, not a filter

The tempting version of `build_registries()` is one dict and a check:

```python
tools = {t.name: t for t in discover_tools()}
...
if tools[name].access == "read":
    return tools[name].run(arguments)
```

That is a filter, and a filter can be wrong in a way nothing catches until it matters — a
misread `!=`, a field renamed on one side and not the other, a fallthrough branch added later
for a case that felt unrelated. `hermes-agent/hermes/tools.py` makes the same argument about
its own two registries, and the reasoning transfers unchanged: a write tool that a handler
*could* call if a check went the wrong way is one bug away from a write tool a handler *can*
call. This example builds two `ToolRegistry` instances instead, one per access level, and each
refuses at `register()` to hold a tool of the other kind. `Toolbelt` is built from the read
registry only, and its constructor refuses anything else. The write registry is never passed to
it — not filtered out of it, never given to it — so "the toolbelt calls a write tool" is not a
check to bypass, it is a reference that does not exist.

## Mutation testing

Ran the mutation `build_registries()` warns against: collapsed both registries into one,
mutating a shared registry's `access` field to whatever tool was last discovered, and made
`Toolbelt.call()` check `tool.access` at call time instead of relying on the registry to refuse
the wrong kind. 6 of the 11 tests in
[`tests/test_tool_discovery.py`](../../tests/test_tool_discovery.py) went red — every test in
`TestTheSplitIsStructural`, plus the duplicate-name registration test — because `Toolbelt`'s own
constructor caught the mutated registry's now-wrong `access` before any call-time filter had a
chance to run. Reverted afterward; `discover.py` as shipped is the unmutated version.

## What is simplified

**A tool's declared `ACCESS` is trusted, not verified against what `run()` actually does.**
Nothing here checks that a tool claiming `"read"` doesn't mutate something — that would need
sandboxing the call itself, which is a different and harder problem. The split this example
demonstrates only holds if the declaration is honest; a `read`-labeled tool that lies is not
something a discovery mechanism can catch by inspecting metadata.

**Importing a file is running it.** `discover_tools()` only ever points at `tools/`, a directory
that ships with this example. Pointing the same function at a directory populated by a download
or a URL, without verifying where that code came from first, would be running untrusted code —
that provenance check is not something this example implements, and copying the loader as-is
into a system that discovers tools from an external source would need it added.

## Related

- [hermes-agent](../hermes-agent/README.md) — the same read/write split, tools declared in code
  rather than discovered
- [BUILDING-BLOCKS.md §2 — Tool layer and API contracts](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md#2--tool-layer-and-api-contracts)

## Security

This example demonstrates the read/write split, the same property `hermes-agent` and
`graph-agent` enforce, but does not itself gate anything against a human approval — there is no
approval flow here, only discovery and the split. See `hermes-agent` for the full enforcement
path from a write proposal to an approved, single-use claim.
