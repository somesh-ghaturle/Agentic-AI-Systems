"""A write tool: restarts a named service.

Exactly the kind of tool that must never reach a handler's toolbelt just because it happened to
be dropped in this directory — see discover.py's build_registries() for why it cannot.
"""

NAME = "restart_service"
ACCESS = "write"
DESCRIPTION = "Restart a named service. Changes state."


def run(arguments: dict) -> dict:
    return {"service": arguments.get("service", "unknown"), "status": "restarted"}
