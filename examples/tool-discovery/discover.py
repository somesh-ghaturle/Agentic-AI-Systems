"""Tool discovery: load tool definitions from a directory instead of hardcoding them, and keep
the read/write split a structural property of the loader rather than a filter over one list.

    python3 discover.py

Every other tool-owning example in this repository (see hermes-agent/hermes/tools.py) declares
its tools in Python at the top of one module. That does not scale to a system where tools
arrive by being dropped in — a plugin directory, an installed package, an MCP server's tool
list — and "arrives by being dropped in" is exactly the case where a write tool reaching a
handler is a one-line accident instead of a typo someone would catch in review.

No dependencies, no model, no key.
"""

from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass
from typing import Any, Callable

READ = "read"
WRITE = "write"
ACCESS_LEVELS = (READ, WRITE)

TOOLS_DIR = pathlib.Path(__file__).resolve().parent / "tools"

REQUIRED_ATTRS = ("NAME", "ACCESS", "DESCRIPTION", "run")


class ToolError(Exception):
    """A tool call was asked for something it cannot do."""


class UnknownTool(ToolError):
    """No read tool by that name — including one that exists, but only as a write tool."""


class DiscoveryError(Exception):
    """A file in the tools directory does not declare a usable tool contract."""


class WriteBoundaryViolation(Exception):
    """A write tool was reached from a path that should never hold a reference to one."""


@dataclass(frozen=True)
class Tool:
    name: str
    access: str
    description: str
    run: Callable[[dict[str, Any]], Any]

    def __post_init__(self) -> None:
        if self.access not in ACCESS_LEVELS:
            raise ValueError(
                f"tool {self.name!r}: access must be one of {ACCESS_LEVELS}, got {self.access!r}"
            )


def _load_module(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(f"tool_discovery.tools.{path.stem}", path)
    if spec is None or spec.loader is None:
        raise DiscoveryError(f"{path}: could not load as a module")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exercised by malformed-file tests in callers
        raise DiscoveryError(f"{path}: failed to import tool module") from exc
    return module


def discover_tools(directory: pathlib.Path = TOOLS_DIR) -> list[Tool]:
    """Import every .py file in `directory` and build a Tool from its declared contract.

    Discovered files declare NAME / ACCESS / DESCRIPTION / run as plain module attributes
    rather than importing Tool from here and constructing one themselves. That sidesteps a
    module-identity trap: a file loaded through spec_from_file_location and a file imported
    the normal way can end up as two different module objects even when they point at the same
    path on disk, so an isinstance() check against a class re-imported that way is not
    reliable. Reading plain attributes off the loaded module has no such failure mode.

    This is also the part a production loader would need to harden further. Importing a file
    is running it, and this only ever points at a directory shipped with the example. Pointing
    it at a directory populated by a download or a URL, without verifying provenance first, is
    not something this function does and should not be copied as if it were.
    """
    tools: list[Tool] = []
    for path in sorted(directory.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = _load_module(path)
        missing = [attr for attr in REQUIRED_ATTRS if not hasattr(module, attr)]
        if missing:
            raise DiscoveryError(f"{path}: missing {missing}")
        tools.append(
            Tool(
                name=module.NAME,
                access=module.ACCESS,
                description=module.DESCRIPTION,
                run=module.run,
            )
        )
    return tools


class ToolRegistry:
    """Holds tools of exactly one access level.

    Same shape as hermes-agent/hermes/tools.py, and the same reason: the write callables live
    in an object a handler is never handed, so "the handler calls a write tool" is not a check
    that can be bypassed, it is a reference the handler does not have.
    """

    def __init__(self, access: str) -> None:
        if access not in ACCESS_LEVELS:
            raise ValueError(f"access must be one of {ACCESS_LEVELS}, got {access!r}")
        self.access = access
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if tool.access != self.access:
            raise WriteBoundaryViolation(
                f"tool {tool.name!r} is {tool.access!r} and cannot be registered "
                f"in the {self.access!r} registry"
            )
        if tool.name in self._tools:
            raise DiscoveryError(f"two discovered tools are both named {tool.name!r}")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise UnknownTool(
                f"no {self.access} tool named {name!r}; have {sorted(self._tools)}"
            ) from None

    def names(self) -> list[str]:
        return sorted(self._tools)

    def __len__(self) -> int:
        return len(self._tools)


def build_registries(tools: list[Tool]) -> tuple[ToolRegistry, ToolRegistry]:
    """Partition discovered tools by declared access into two separate registries.

    This line is the one that matters, and it is deliberately not `{t.name: t for t in tools}`
    plus an `access == "read"` check at call time. A single dict filtered at call time is a
    filter — one bad conditional, one renamed field, and a write tool is reachable through it.
    Two registries, each refusing to hold the other's access level, turn that mistake into a
    WriteBoundaryViolation at *registration* time instead of a silent hole at call time.
    """
    read_registry = ToolRegistry(READ)
    write_registry = ToolRegistry(WRITE)
    for tool in tools:
        (read_registry if tool.access == READ else write_registry).register(tool)
    return read_registry, write_registry


class Toolbelt:
    """What a handler is given: read tools only, built from a registry that cannot hold a
    write tool in the first place.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        if registry.access != READ:
            raise WriteBoundaryViolation("a toolbelt must be built from the read registry")
        self._registry = registry

    @property
    def available(self) -> list[str]:
        return self._registry.names()

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        tool = self._registry.get(name)
        if tool.access != READ:
            raise WriteBoundaryViolation(
                f"tool {name!r} is {tool.access!r}; handlers may only call read tools"
            )
        return tool.run(dict(arguments or {}))


def main() -> None:
    tools = discover_tools()
    read_registry, write_registry = build_registries(tools)
    toolbelt = Toolbelt(read_registry)

    print(f"discovered {len(tools)} tool(s) in {TOOLS_DIR.name}/")
    print(f"read tools available to a handler:   {toolbelt.available}")
    print(f"write tools discovered but withheld: {write_registry.names()}")

    result = toolbelt.call("get_weather", {"city": "Boston"})
    print(f"toolbelt.call('get_weather', {{'city': 'Boston'}}) -> {result}")

    for name in write_registry.names():
        try:
            toolbelt.call(name)
        except UnknownTool as exc:
            print(f"toolbelt.call({name!r}) refused: {exc}")


if __name__ == "__main__":
    main()
