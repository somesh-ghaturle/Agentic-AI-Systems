"""Tests the documented-counts guard: stale numbers fail, and so does a reworded sentence.

    python3 -m unittest tests.test_docs_counts -v

docs_counts.py had no suite (task 89), though it now checks 39 claims across nine files.
Every claim added in tasks 77, 81, 82 and 83 was mutation-tested once, by hand, and nothing
re-ran those mutations afterwards.

The end-to-end tests run the script over a trimmed copy of this repository, change one
documented number, and expect the failure. The copy's own `tests/` is not discovered: loading
a second directory of same-named test modules inside a running test process collides with the
ones already imported. So the real tree's test counts are computed once and reused, and a
separate test checks that computation against unittest's own discovery.
"""

import contextlib
import importlib.util
import io
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "docs_counts.py"

_spec = importlib.util.spec_from_file_location("docs_counts", SCRIPT)
docs_counts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(docs_counts)


class TestReadingNumbers(unittest.TestCase):
    """Prose writes small numbers as words; tables as digits. Both must parse."""

    def test_digits_units_tens_and_compounds(self):
        for token, value in (("24", 24), ("nine", 9), ("twenty", 20), ("twenty-four", 24),
                             ("Forty-Four", 44), ("zero", 0), ("nineteen", 19)):
            with self.subTest(token=token):
                self.assertEqual(docs_counts.to_int(token), value)

    def test_trailing_punctuation_is_ignored(self):
        self.assertEqual(docs_counts.to_int("twelve,"), 12)

    def test_what_is_not_a_number_is_none(self):
        for token in ("many", "twenty-ten", "forty-zero", "", "4a"):
            with self.subTest(token=token):
                self.assertIsNone(docs_counts.to_int(token))


class TestCountingTests(unittest.TestCase):
    def test_the_count_matches_unittests_own_discovery(self):
        expected = unittest.defaultTestLoader.discover(str(REPO / "tests")).countTestCases()
        self.assertEqual(docs_counts.test_counts(REPO)["tests"], expected)

    def test_a_module_that_fails_to_import_stops_the_check(self):
        """Counted as one test, it would pass silently with the wrong total."""
        with tempfile.TemporaryDirectory() as d:
            tests = pathlib.Path(d) / "tests"
            tests.mkdir()
            (tests / "test_docs_counts_broken_fixture.py").write_text("import no_such_module\n")
            with self.assertRaises(SystemExit):
                docs_counts.test_counts(pathlib.Path(d))


class TestAgainstACopyOfTheTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls._tmp.name) / "repo"
        shutil.copytree(REPO, cls.root, ignore=shutil.ignore_patterns(
            ".git", "graphify-out", "node_modules", ".terraform", "__pycache__",
            ".venv", "venv", "*.gif", "*.zip",
        ))
        real = docs_counts.test_counts(REPO)
        cls._patch = mock.patch.object(docs_counts, "test_counts", return_value=real)
        cls._patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._patch.stop()
        cls._tmp.cleanup()

    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = docs_counts.main(self.root)
        return code, out.getvalue()

    @contextlib.contextmanager
    def edited(self, rel, old, new):
        path = self.root / rel
        original = path.read_text()
        self.assertIn(old, original, f"anchor missing in {rel}")
        path.write_text(original.replace(old, new, 1))
        try:
            yield
        finally:
            path.write_text(original)

    def test_the_copy_passes(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_a_stale_table_number_fails(self):
        with self.edited("ROADMAP.md", "| Examples | 24,", "| Examples | 23,"):
            code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("claims 23 examples, tree has 24", out)

    def test_a_stale_number_written_as_words_fails(self):
        with self.edited("README.md", "syntax check over all twenty-four examples",
                         "syntax check over all twenty-three examples"):
            code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("claims twenty-three examples, tree has 24", out)

    def test_a_reworded_sentence_fails_rather_than_skipping(self):
        with self.edited("ROADMAP.md", "| Tests |", "| Test cases |"):
            code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("no longer matches its pattern", out)

    def test_the_tree_moving_under_the_docs_fails(self):
        extra = self.root / "examples" / "a-new-example"
        extra.mkdir()
        try:
            code, out = self.run_check()
        finally:
            extra.rmdir()
        self.assertEqual(code, 1)
        self.assertIn("tree has 25", out)

    def test_a_per_tree_module_count_fails(self):
        """Task 83's claim: the overview table, not only the expected-output block."""
        with self.edited("infra/MODULES.md", "| AWS | 9 |", "| AWS | 8 |"):
            code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("claims 8 aws modules (overview), tree has 9", out)


if __name__ == "__main__":
    unittest.main()
