"""Focused tests for the dependency-free memory example."""

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "memory_example", ROOT / "examples/memory-agent" / "memory.py"
)
memory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = memory
SPEC.loader.exec_module(memory)


class TestVectorMemory(unittest.TestCase):
    def test_search_returns_nearest_metadata(self):
        store = memory.VectorMemory(embedding_dim=2)
        store.add("near", [1, 0], {"id": "near"})
        store.add("far", [0, 1], {"id": "far"})
        self.assertEqual(store.search([1, 0], 1)[0]["metadata"]["id"], "near")

    def test_dimension_is_enforced(self):
        with self.assertRaises(ValueError):
            memory.VectorMemory(2).add("bad", [1])


class TestDecayAndSessions(unittest.TestCase):
    def test_decay_removes_old_values(self):
        now = [0.0]
        store = memory.TimeDecayMemory(half_life=1, clock=lambda: now[0])
        store.add("key", "value")
        now[0] = 4
        self.assertIsNone(store.get("key"))

    def test_session_is_required_and_recorded(self):
        store = memory.SessionMemory(embedding_dim=1)
        with self.assertRaises(RuntimeError):
            store.remember("fact", [1])
        store.start("session-1")
        store.remember("fact", [1])
        self.assertEqual(store.recall([1])[0]["metadata"]["session_id"], "session-1")


class TestGraphMemory(unittest.TestCase):
    def test_relationships_are_copied(self):
        graph = memory.GraphMemory()
        graph.add_relationship("a", "uses", "b")
        related = graph.related("a", "uses")
        related.add("c")
        self.assertEqual(graph.related("a", "uses"), {"b"})


if __name__ == "__main__":
    unittest.main()
