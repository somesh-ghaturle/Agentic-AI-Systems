"""A read tool: looks something up, changes nothing."""

NAME = "get_weather"
ACCESS = "read"
DESCRIPTION = "Look up a forecast for a city. Read-only."


def run(arguments: dict) -> dict:
    return {"city": arguments.get("city", "unknown"), "forecast": "sunny, 72F"}
