"""Tests for the example dependency check.

    python3 -m unittest tests.test_example_deps -v

The check exists to catch a dependency an example imports but does not pin. If its own name
matching quietly breaks it reports success on everything, which is worse than not having it —
the same reason tests/test_tfconstraints.py exists for the provider-pin guard.

Most of these are about name matching, because that is where the false negatives live. An
import name and a distribution name agree often enough that a naive comparison looks correct
right up until it meets `faiss` and `faiss-cpu`.
"""

import importlib.util
import pathlib
import tempfile
import unittest

SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent / ".github" / "scripts" / "example_deps.py"
)
spec = importlib.util.spec_from_file_location("example_deps", SCRIPT)
deps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deps)


class TestNormalise(unittest.TestCase):
    """PEP 503: lowercase, and runs of -_. collapse to a single dash."""

    def test_underscores_become_dashes(self):
        self.assertEqual(deps.normalise("typing_extensions"), "typing-extensions")
        self.assertEqual(deps.normalise("langchain_core"), "langchain-core")

    def test_case_is_folded(self):
        self.assertEqual(deps.normalise("FastAPI"), "fastapi")

    def test_runs_collapse(self):
        self.assertEqual(deps.normalise("a__b"), "a-b")
        self.assertEqual(deps.normalise("a._-b"), "a-b")

    def test_already_normal_is_unchanged(self):
        self.assertEqual(deps.normalise("faiss-cpu"), "faiss-cpu")


class TestDeclared(unittest.TestCase):
    """Requirements syntax that has to come off before names can be compared."""

    def _write(self, text):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "requirements.txt"
        tmp.write_text(text)
        return deps.declared(tmp)

    def test_version_specifiers_are_stripped(self):
        self.assertEqual(self._write("fastapi==0.141.1"), {"fastapi"})
        self.assertEqual(self._write("numpy>=2.0"), {"numpy"})
        self.assertEqual(self._write("ray~=2.57"), {"ray"})

    def test_extras_are_stripped(self):
        self.assertEqual(self._write("uvicorn[standard]==0.52.3"), {"uvicorn"})
        self.assertEqual(self._write("ray[default]==2.57.0"), {"ray"})

    def test_comments_and_blanks_are_ignored(self):
        self.assertEqual(self._write("# a note\n\nfastapi==1.0\n"), {"fastapi"})

    def test_trailing_comment_on_a_pin(self):
        self.assertEqual(self._write("fastapi==1.0  # why"), {"fastapi"})

    def test_a_missing_file_declares_nothing(self):
        self.assertEqual(deps.declared(pathlib.Path("/nonexistent/requirements.txt")), set())


class TestSatisfiedBy(unittest.TestCase):
    """Where import name and distribution name diverge."""

    def test_exact_match(self):
        self.assertTrue(deps.satisfied_by("fastapi", {"fastapi"}))

    def test_normalisation_bridges_underscores(self):
        self.assertTrue(deps.satisfied_by("typing_extensions", {"typing-extensions"}))

    def test_irregular_names_need_the_alias_table(self):
        self.assertTrue(deps.satisfied_by("faiss", {"faiss-cpu"}))
        self.assertFalse(deps.satisfied_by("faiss", {"faiss-something-else"}))

    def test_a_namespace_package_accepts_any_mapped_distribution(self):
        self.assertTrue(deps.satisfied_by("opentelemetry", {"opentelemetry-api"}))
        self.assertTrue(deps.satisfied_by("opentelemetry", {"opentelemetry-sdk"}))

    def test_an_unpinned_import_is_not_satisfied(self):
        self.assertFalse(deps.satisfied_by("langgraph", set()))


class TestImported(unittest.TestCase):
    """ast rather than regex, which is what makes guarded imports visible."""

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())

    def _found(self, source):
        (self.dir / "m.py").write_text(source)
        return deps.imported(self.dir)

    def test_a_guarded_import_is_still_an_import(self):
        """The typing_extensions finding lived inside a try/except. A regex over top-level
        lines would have missed it, and did."""
        found = self._found("try:\n    import langgraph\nexcept ImportError:\n    pass\n")
        self.assertIn("langgraph", found)

    def test_an_import_inside_a_function_counts(self):
        self.assertIn("ray", self._found("def f():\n    import ray\n"))

    def test_submodules_resolve_to_their_top_level_name(self):
        found = self._found("from opentelemetry.sdk.trace import X\nimport a.b.c\n")
        self.assertIn("opentelemetry", found)
        self.assertIn("a", found)
        self.assertNotIn("opentelemetry.sdk", found)

    def test_relative_imports_are_not_dependencies(self):
        self.assertEqual(self._found("from . import sibling\n"), {})

    def test_the_importing_file_is_reported(self):
        found = self._found("import ray\n")
        self.assertEqual([p.name for p in found["ray"]], ["m.py"])


class TestFindCycle(unittest.TestCase):
    """The graph that can actually cycle: example to example."""

    def test_a_dag_has_no_cycle(self):
        self.assertIsNone(deps.find_cycle({"a": {"b"}, "b": {"c"}, "c": set()}))

    def test_the_current_repository_shape_is_acyclic(self):
        """trace-eval imports hermes-agent and nothing imports trace-eval."""
        self.assertIsNone(deps.find_cycle({"trace-eval": {"hermes-agent"}, "hermes-agent": set()}))

    def test_a_two_node_cycle_is_found(self):
        cycle = deps.find_cycle({"a": {"b"}, "b": {"a"}})
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle[0], cycle[-1])

    def test_a_longer_cycle_is_found(self):
        cycle = deps.find_cycle({"a": {"b"}, "b": {"c"}, "c": {"a"}})
        self.assertIsNotNone(cycle)
        self.assertEqual(set(cycle), {"a", "b", "c"})

    def test_a_cycle_is_found_when_it_is_not_at_the_root(self):
        """A cycle downstream of an acyclic entry point still has to be reported."""
        cycle = deps.find_cycle({"a": {"b"}, "b": {"c"}, "c": {"b"}})
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle[0], cycle[-1])

    def test_a_self_loop_is_a_cycle(self):
        self.assertIsNotNone(deps.find_cycle({"a": {"a"}}))

    def test_shared_dependencies_are_not_a_cycle(self):
        """Two examples importing the same third one is a diamond, not a loop."""
        self.assertIsNone(deps.find_cycle({"a": {"c"}, "b": {"c"}, "c": set()}))


class TestEndToEnd(unittest.TestCase):
    """The check against a tree built to fail, then fixed."""

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp()) / "examples"
        (self.root / "one").mkdir(parents=True)

    def _run(self):
        return deps.check(self.root)

    def test_an_unpinned_import_fails(self):
        (self.root / "one" / "a.py").write_text("import ray\n")
        (self.root / "one" / "requirements.txt").write_text("")
        self.assertEqual(self._run(), 1)

    def test_pinning_it_passes(self):
        (self.root / "one" / "a.py").write_text("import ray\n")
        (self.root / "one" / "requirements.txt").write_text("ray[default]==2.57.0\n")
        self.assertEqual(self._run(), 0)

    def test_stdlib_needs_no_pin(self):
        (self.root / "one" / "a.py").write_text("import json\nimport pathlib\n")
        self.assertEqual(self._run(), 0)

    def test_a_sibling_module_needs_no_pin(self):
        (self.root / "one" / "a.py").write_text("import helper\n")
        (self.root / "one" / "helper.py").write_text("")
        self.assertEqual(self._run(), 0)

    def test_a_cross_example_import_is_an_edge_not_a_failure(self):
        (self.root / "two").mkdir()
        (self.root / "two" / "lib.py").write_text("")
        (self.root / "one" / "a.py").write_text("import lib\n")
        self.assertEqual(self._run(), 0)

    def test_a_cycle_between_examples_fails(self):
        (self.root / "two").mkdir()
        (self.root / "one" / "one_lib.py").write_text("import two_lib\n")
        (self.root / "two" / "two_lib.py").write_text("import one_lib\n")
        self.assertEqual(self._run(), 1)


class TestTheRealTree(unittest.TestCase):
    """The check has to pass on this repository, or it is not wired up honestly."""

    def test_examples_pass(self):
        root = pathlib.Path(__file__).resolve().parent.parent / "examples"
        self.assertEqual(deps.check(root), 0)


if __name__ == "__main__":
    unittest.main()
