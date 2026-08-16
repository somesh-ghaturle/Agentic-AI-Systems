"""Tools, split by access, and the two registries that keep the split honest.

The split is the whole design. A tool is `read` or `write`, and that word decides which
registry holds its callable. `ToolRegistry` is not a filter over one big table with an
`access` column — the write callables live in an object the router is never handed, so
"the router calls a write tool" is not a check that can be bypassed, it is a reference the
router does not have.

That is the same shape as the AWS tree's two independent locks: an access check *and* a
missing reference, either one sufficient. Losing one leaves the other standing. See
`infra/terraform-aws/tests/test_write_boundary.py` for the infrastructure counterpart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

READ = "read"
WRITE = "write"
ACCESS_LEVELS = (READ, WRITE)


class ToolError(Exception):
    """A tool was asked for something it cannot do. Distinct from a boundary violation."""


class UnknownTool(ToolError):
    """No tool by that name in the registry being asked."""


class WriteBoundaryViolation(Exception):
    """A write tool was reached from a path that is not allowed to reach it.

    Its own exception type, not a `ValueError`, so a caller cannot swallow it with a broad
    `except ToolError` while handling ordinary tool failures. This one should reach the top
    and fail the request loudly.
    """


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


class ToolRegistry:
    """A registry that holds tools of exactly one access level.

    The constructor takes the level and rejects anything else on registration, so a write
    tool cannot be added to the read registry by a caller who was not thinking about it.
    That mistake — a one-word edit that reads as a simplification — is the one this guards.
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
            raise ValueError(f"tool {tool.name!r} is already registered")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise UnknownTool(
                f"no {self.access} tool named {name!r}; have {sorted(self._tools)}"
            ) from None

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)

    def __len__(self) -> int:
        return len(self._tools)


class Toolbelt:
    """What a handler is given. Read tools only, and it cannot be talked out of that.

    A handler never receives the write registry. When it wants a write it returns a
    proposal (see `router.py`) and the request stops there until a human approves that
    specific action.
    """

    def __init__(self, registry: ToolRegistry, tracer=None) -> None:
        if registry.access != READ:
            raise WriteBoundaryViolation(
                "a toolbelt handed to a handler must be built from the read registry"
            )
        self._registry = registry
        self._tracer = tracer

    @property
    def available(self) -> list[str]:
        return self._registry.names()

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        arguments = dict(arguments or {})
        tool = self._registry.get(name)
        # Belt and braces: the registry cannot hold a write tool, and this refuses one
        # anyway. If the invariant above is ever broken, the failure is this line rather
        # than a write executing without an approval.
        if tool.access != READ:
            raise WriteBoundaryViolation(
                f"tool {name!r} is {tool.access!r}; handlers may only call read tools"
            )
        if self._tracer is not None:
            self._tracer.emit("tool.call", tool=name, access=READ, arguments=arguments)
        result = tool.run(arguments)
        if self._tracer is not None:
            self._tracer.emit("tool.result", tool=name, access=READ)
        return result
