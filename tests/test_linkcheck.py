"""Tests the relative-link checker CI trusts to keep 134 markdown files navigable.

    python3 -m unittest tests.test_linkcheck -v

linkcheck.py had no suite (task 89). Its docstring records that the first version reported 34
broken links, all of them false positives, from fenced code blocks and #fragment suffixes.
Those two cases are the ones pinned here, along with the broken link it exists to catch.
Each test builds a small tree in a temp dir and runs the script as CI does.
"""

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "linkcheck.py"

_spec = importlib.util.spec_from_file_location("linkcheck", SCRIPT)
linkcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(linkcheck)


def run(root):
    r = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
    return r.returncode, r.stdout


class LinkCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        (self.root / "target.md").write_text("# Target\n")
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def broken(self, text, name="doc.md"):
        return list(linkcheck.broken_links(self.write(name, text)))


class TestWhatItCatches(LinkCheckTest):
    def test_a_link_to_a_missing_file_is_reported_with_its_line(self):
        self.write("doc.md", "intro\n\nsee [gone](missing.md)\n")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("BROKEN doc.md:3 -> missing.md", out)

    def test_a_link_into_a_missing_directory_is_reported(self):
        self.assertEqual(self.broken("[x](nope/target.md)\n"), [(1, "nope/target.md")])

    def test_a_valid_relative_link_passes(self):
        self.write("doc.md", "[ok](target.md)\n")
        self.assertEqual(run(self.root)[0], 0)

    def test_links_resolve_against_the_linking_file(self):
        self.assertEqual(self.broken("[up](../target.md)\n", name="sub/doc.md"), [])
        self.assertEqual(self.broken("[here](target.md)\n", name="sub/doc.md"),
                         [(1, "target.md")])


class TestTheFalsePositivesItWasBuiltToAvoid(LinkCheckTest):
    def test_a_fragment_suffix_is_stripped_before_the_path_check(self):
        self.assertEqual(self.broken("[s](target.md#some-section)\n"), [])

    def test_a_fragment_on_a_missing_file_is_still_broken(self):
        self.assertEqual(self.broken("[s](gone.md#x)\n"), [(1, "gone.md#x")])

    def test_links_inside_backtick_fences_are_skipped(self):
        self.assertEqual(self.broken("```md\n[q](quoted.md)\n```\n"), [])

    def test_links_inside_tilde_fences_are_skipped(self):
        self.assertEqual(self.broken("~~~\n[q](quoted.md)\n~~~\n"), [])

    def test_checking_resumes_after_a_fence_closes(self):
        self.assertEqual(self.broken("```\n[q](quoted.md)\n```\n[b](gone.md)\n"),
                         [(4, "gone.md")])

    def test_external_and_anchor_links_are_not_checked(self):
        text = "[a](https://x.invalid/y.md) [b](mailto:a@b.c) [c](#local) [d](tel:1)\n"
        self.assertEqual(self.broken(text), [])

    def test_a_link_title_is_not_part_of_the_path(self):
        self.assertEqual(self.broken('[t](target.md "Title")\n'), [])

    def test_skipped_directories_are_not_scanned(self):
        self.write("node_modules/pkg/README.md", "[x](gone.md)\n")
        self.assertEqual(run(self.root)[0], 0)


class TestTheRealTree(unittest.TestCase):
    def test_the_repository_has_no_broken_relative_links(self):
        code, out = run(REPO)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
