"""Tests the docs preview generator.

    python3 -m unittest tests.test_docs_preview -v
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "docs_preview.py"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(root, out_dir):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), str(out_dir)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


class TestDocsPreview(unittest.TestCase):
    def test_generates_preview_pages(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write(root / "README.md", "# Root\n\nSee [docs](docs/guide.md).\n")
            write(root / "docs" / "guide.md", "# Guide\n\n- one\n- two\n")
            out = root / "site"
            code, out_text = run(root, out)
            self.assertEqual(0, code, out_text)
            self.assertTrue((out / "index.html").exists())
            self.assertTrue((out / "README.html").exists())
            self.assertTrue((out / "docs" / "guide.html").exists())
            index_html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Documentation preview", index_html)
            self.assertIn("Root", index_html)

    def test_ignores_vendor_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write(root / ".git" / "ignored.md", "# Ignore me\n")
            write(root / "docs" / "kept.md", "# Kept\n")
            out = root / "site"
            code, out_text = run(root, out)
            self.assertEqual(0, code, out_text)
            self.assertTrue((out / "docs" / "kept.html").exists())
            self.assertFalse((out / ".git" / "ignored.html").exists())

    def test_repo_preview_builds(self):
        # The repo-root build is the one this test exists to guard, but writing the
        # output into the repo root leaves generated HTML in the worktree after the
        # run. Use a temp directory for the output so the build is exercised without
        # staging artifacts the .gitignore is there to catch when someone runs the
        # script by hand.
        with tempfile.TemporaryDirectory() as d:
            out_dir = pathlib.Path(d)
            code, out_text = run(REPO, out_dir)
            self.assertEqual(0, code, out_text)
            self.assertTrue((out_dir / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
