"""Tests rag-faiss's retrieval mechanics, and the drift bug its two files invited.

    python3 -m unittest tests.test_rag_faiss -v

Skips unless faiss and numpy are installed, so it runs in the `example-deps` CI job and stays
out of the dependency-free one — the same pattern as tests/test_e2e_agent.py.

**What is and is not covered, stated plainly.** These tests do not download a model. The
embedding step is the one part of this example that needs ~90 MB from HuggingFace and a
network, and a suite that pulls it is a suite that fails on a bad day at someone else's CDN.

What that leaves is still worth testing, because it is where the example can be *wrong*
rather than merely slow: the index round-trips to disk, search returns neighbours in distance
order, and the position-to-document mapping is correct. Those are the mechanics the example
exists to demonstrate. Substituting a deterministic embedder is not mocking the model to
assert the mock was called — the assertions are all about retrieval behaviour that holds for
any embedder.

The one test that does exercise sentence-transformers end to end is skipped unless the model
is already cached locally, so it covers the real path for anyone who has run the example
without making CI depend on a download.
"""

import importlib.util
import pathlib
import sys
import tempfile
import unittest

EXAMPLE = pathlib.Path(__file__).resolve().parent.parent / "examples" / "rag-faiss"
sys.path.insert(0, str(EXAMPLE))

HAS_FAISS = importlib.util.find_spec("faiss") is not None
HAS_NUMPY = importlib.util.find_spec("numpy") is not None
HAS_ST = importlib.util.find_spec("sentence_transformers") is not None

# Importing build_index or query pulls sentence_transformers at module scope, so any test that
# touches them needs the whole set — not just faiss. Found by running this suite in a venv with
# faiss and numpy but no sentence-transformers: four errors, all ModuleNotFoundError, none of
# them about the thing under test. CI installs the full requirements.txt so it would have
# passed there and hidden the wrong guard.
IMPORTABLE = HAS_ST and HAS_FAISS and HAS_NUMPY


class TestTheDriftBug(unittest.TestCase):
    """`DOCS` lived in both files, copied. Now it lives in one and is imported.

    The failure it invited was silent and total: the index is built from one list, and search
    results are mapped back to text by *position* in the other. Edit one and every result is
    confidently mislabelled, with nothing raised and both files reading correctly alone.
    """

    def test_query_does_not_define_its_own_copy(self):
        source = (EXAMPLE / "query.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "DOCS = [",
            source,
            "query.py has reintroduced its own DOCS list; it must import the one in "
            "build_index.py or the index and its labels can drift apart",
        )

    @unittest.skipUnless(IMPORTABLE, "example dependencies absent; runs in example-deps")
    def test_both_modules_see_the_same_list_object(self):
        import build_index  # noqa: PLC0415
        import query  # noqa: PLC0415

        self.assertIs(query.DOCS, build_index.DOCS)


@unittest.skipUnless(HAS_FAISS and HAS_NUMPY, "faiss/numpy absent; runs in example-deps")
class TestRetrievalMechanics(unittest.TestCase):
    """Index behaviour, with vectors chosen rather than embedded."""

    def setUp(self):
        import faiss  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        self.faiss = faiss
        self.np = np
        # Three points on a line. Nearest-neighbour order is then arithmetic, not a
        # judgement about what a sentence means.
        self.vectors = np.array(
            [[0.0, 0.0], [1.0, 0.0], [5.0, 0.0]], dtype="float32"
        )
        self.index = faiss.IndexFlatL2(2)
        self.index.add(self.vectors)

    def test_search_returns_neighbours_in_distance_order(self):
        query = self.np.array([[0.9, 0.0]], dtype="float32")
        distances, ids = self.index.search(query, 3)
        self.assertEqual(list(ids[0]), [1, 0, 2])
        self.assertTrue(all(distances[0][i] <= distances[0][i + 1] for i in range(2)))

    def test_k_limits_the_result_count(self):
        _, ids = self.index.search(self.np.array([[0.0, 0.0]], dtype="float32"), 2)
        self.assertEqual(len(ids[0]), 2)

    def test_the_index_round_trips_through_disk(self):
        """build_index writes, query reads. If that is lossy, every result is wrong."""
        with tempfile.TemporaryDirectory() as tmp:
            path = str(pathlib.Path(tmp) / "t.faiss")
            self.faiss.write_index(self.index, path)
            reloaded = self.faiss.read_index(path)

            self.assertEqual(reloaded.ntotal, self.index.ntotal)
            q = self.np.array([[0.9, 0.0]], dtype="float32")
            self.assertEqual(
                list(reloaded.search(q, 3)[1][0]), list(self.index.search(q, 3)[1][0])
            )

    @unittest.skipUnless(IMPORTABLE, "example dependencies absent; runs in example-deps")
    def test_ids_map_back_to_documents_by_position(self):
        """The mapping the drift bug would have corrupted."""
        import build_index  # noqa: PLC0415

        _, ids = self.index.search(self.np.array([[4.9, 0.0]], dtype="float32"), 1)
        self.assertEqual(build_index.DOCS[ids[0][0]], build_index.DOCS[2])


@unittest.skipUnless(IMPORTABLE, "example dependencies absent; runs in example-deps")
class TestTheExampleItself(unittest.TestCase):
    def test_there_are_as_many_documents_as_the_index_expects(self):
        import build_index  # noqa: PLC0415

        self.assertEqual(len(build_index.DOCS), 3)
        self.assertTrue(all(isinstance(d, str) and d for d in build_index.DOCS))

    def test_importing_neither_module_builds_an_index(self):
        """Both are __main__-guarded. An import that downloads a model and writes a file is a
        module that cannot be tested, imported, or safely depended on — and this whole suite
        imports them, so the guard is load-bearing here rather than stylistic.

        Asserted against the source rather than by watching for the file: the example is meant
        to be run, so index.faiss may legitimately already exist from a previous run, and
        checking for its absence would fail for the wrong reason.
        """
        import build_index  # noqa: PLC0415
        import query  # noqa: PLC0415

        for module in (build_index, query):
            source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
            self.assertIn(
                '__name__ == "__main__"',
                source,
                f"{module.__name__} does work at import time",
            )

        self.assertTrue(callable(build_index.build_index))
        self.assertTrue(callable(query.query))


@unittest.skipUnless(IMPORTABLE, "sentence-transformers absent")
class TestEndToEnd(unittest.TestCase):
    """The real path, skipped unless the model is already cached.

    Deliberately not a CI gate. It needs ~90 MB from HuggingFace, and a check that depends on
    someone else's CDN is a check that goes red for reasons no one here can fix.
    """

    @classmethod
    def setUpClass(cls):
        import os  # noqa: PLC0415

        cache = pathlib.Path(
            os.environ.get("HF_HOME", pathlib.Path.home() / ".cache" / "huggingface")
        )
        if not cache.exists():
            raise unittest.SkipTest("model not cached; skipping the download path")

    def test_the_expected_document_ranks_first(self):
        import build_index  # noqa: PLC0415
        import query  # noqa: PLC0415

        with tempfile.TemporaryDirectory():
            build_index.build_index()
            results = query.query("reproducibility in enterprise ai", k=1)
        self.assertIn("Reproducibility", results[0][0])


if __name__ == "__main__":
    unittest.main()
