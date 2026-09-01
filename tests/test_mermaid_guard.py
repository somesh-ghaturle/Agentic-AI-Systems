"""Tests the Mermaid source guard.

    python3 -m unittest tests.test_mermaid_guard -v
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "mermaid_guard.py"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(directory):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(directory)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


class TestMermaidSourceGuard(unittest.TestCase):
    def test_repo_layout_passes(self):
        code, out = run(REPO)
        self.assertEqual(0, code, out)

    def test_rejects_mmd_files(self):
        with tempfile.TemporaryDirectory() as d:
            write(pathlib.Path(d) / "diagram.mmd", "graph TD\nA-->B\n")
            code, out = run(d)
        self.assertEqual(1, code, out)
        self.assertIn("MMD_FILE", out)

    def test_rejects_empty_mermaid_block(self):
        with tempfile.TemporaryDirectory() as d:
            write(pathlib.Path(d) / "README.md", "```mermaid\n```\n")
            code, out = run(d)
        self.assertEqual(1, code, out)
        self.assertIn("MERMAID", out)

    def test_accepts_non_empty_mermaid_block(self):
        with tempfile.TemporaryDirectory() as d:
            write(pathlib.Path(d) / "README.md", "```mermaid\nflowchart LR\nA-->B\n```\n")
            code, out = run(d)
        self.assertEqual(0, code, out)


if __name__ == "__main__":
    unittest.main()
