"""Locks in the discovery contract and the read/write split it feeds.

    python3 -m unittest tests.test_tool_discovery -v

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "tool-discovery"),
)

import discover as td


class TestDiscovery(unittest.TestCase):
    """discover_tools() against the shipped tools/ directory."""

    def test_finds_exactly_the_shipped_tools(self):
        tools = td.discover_tools()
        self.assertEqual(
            {t.name for t in tools}, {"get_weather", "list_orders", "restart_service"}
        )

    def test_access_levels_match_the_files(self):
        by_name = {t.name: t for t in td.discover_tools()}
        self.assertEqual(by_name["get_weather"].access, td.READ)
        self.assertEqual(by_name["list_orders"].access, td.READ)
        self.assertEqual(by_name["restart_service"].access, td.WRITE)

    def test_run_is_callable_and_wired_to_the_right_module(self):
        by_name = {t.name: t for t in td.discover_tools()}
        self.assertEqual(by_name["get_weather"].run({"city": "Reno"})["city"], "Reno")


class TestDiscoveryErrors(unittest.TestCase):
    """A malformed file in the tools directory fails loudly, not silently."""

    def _write(self, directory, filename, content):
        path = pathlib.Path(directory) / filename
        path.write_text(content)
        return path

    def test_a_file_missing_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(
                tmp,
                "broken.py",
                'NAME = "broken"\nACCESS = "read"\nDESCRIPTION = "no run()"\n',
            )
            with self.assertRaises(td.DiscoveryError):
                td.discover_tools(pathlib.Path(tmp))

    def test_an_invalid_access_level_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(
                tmp,
                "sideways.py",
                'NAME = "sideways"\nACCESS = "delete"\nDESCRIPTION = "not read or write"\n'
                "def run(arguments):\n    return None\n",
            )
            with self.assertRaises(ValueError):
                td.discover_tools(pathlib.Path(tmp))

    def test_two_tools_with_the_same_name_fail_at_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            for filename in ("a.py", "b.py"):
                self._write(
                    tmp,
                    filename,
                    'NAME = "dupe"\nACCESS = "read"\nDESCRIPTION = "collides"\n'
                    "def run(arguments):\n    return None\n",
                )
            tools = td.discover_tools(pathlib.Path(tmp))
            with self.assertRaises(td.DiscoveryError):
                td.build_registries(tools)


class TestTheSplitIsStructural(unittest.TestCase):
    """The property the example exists to demonstrate: a write tool is not reachable from a
    Toolbelt, not merely disallowed by one."""

    def setUp(self):
        self.tools = td.discover_tools()
        self.read_registry, self.write_registry = td.build_registries(self.tools)
        self.toolbelt = td.Toolbelt(self.read_registry)

    def test_read_tools_are_available_and_callable(self):
        self.assertEqual(self.toolbelt.available, ["get_weather", "list_orders"])
        self.assertEqual(self.toolbelt.call("get_weather", {"city": "Boston"})["city"], "Boston")

    def test_the_write_tool_is_not_in_the_toolbelt(self):
        self.assertNotIn("restart_service", self.toolbelt.available)

    def test_calling_the_write_tool_by_name_is_refused(self):
        with self.assertRaises(td.UnknownTool):
            self.toolbelt.call("restart_service")

    def test_call_refuses_a_write_tool_even_if_the_registry_is_tampered(self):
        self.read_registry._tools["restart_service"] = self.write_registry.get("restart_service")
        with self.assertRaises(td.WriteBoundaryViolation):
            self.toolbelt.call("restart_service")

    def test_a_toolbelt_cannot_be_built_from_the_write_registry(self):
        with self.assertRaises(td.WriteBoundaryViolation):
            td.Toolbelt(self.write_registry)

    def test_registering_a_write_tool_into_the_read_registry_is_refused(self):
        write_tool = self.write_registry.get("restart_service")
        with self.assertRaises(td.WriteBoundaryViolation):
            self.read_registry.register(write_tool)


if __name__ == "__main__":
    unittest.main()
