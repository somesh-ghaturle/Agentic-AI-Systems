"""Tests the docs preview generator.

    python3 -m unittest tests.test_docs_preview -v
"""

import collections
import pathlib
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser

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


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = collections.defaultdict(list)

    def handle_starttag(self, tag, attrs):
        self.tags[tag].append({k: (v or "") for k, v in attrs})


def collect_tags(markup):
    parser = TagCollector()
    parser.feed(markup)
    return parser.tags


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

    def test_markdown_link_cannot_inject_html_attributes(self):
        # The generated page is served to whoever opens the preview, so a link URL is
        # attacker-controlled text landing inside a quoted href. Both halves matter: the
        # quote must not close the attribute and add a second one, and the scheme must not
        # be executable. Parse the result rather than substring-matching it -- the escaped
        # text "onmouseover=" inside an href value is inert, and only a real parser can
        # tell that apart from an attribute of the same name.
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write(
                root / "README.md",
                "# Root\n\n"
                '[break](" onmouseover="alert(1))\n\n'
                "[js](javascript:alert(1))\n\n"
                "[tab](java\tscript:alert(1))\n\n"
                "[data](data:text/html,hi)\n\n"
                "[fine](https://example.com/a?b=1&c=2)\n\n"
                "[rel](docs/guide.md)\n",
            )
            write(root / "docs" / "guide.md", "# Guide\n")
            out = root / "site"
            code, out_text = run(root, out)
            self.assertEqual(0, code, out_text)

            page = (out / "README.html").read_text(encoding="utf-8")
            anchors = collect_tags(page)["a"]
            for attrs in anchors:
                self.assertEqual(
                    [], [k for k in attrs if k.startswith("on")], f"event handler in {attrs}"
                )
                href = attrs.get("href", "")
                scheme = href.split(":", 1)[0].lower() if ":" in href.split("/", 1)[0] else ""
                self.assertIn(scheme, ("", "http", "https", "mailto", "tel"), href)

            # The safe links still survive the sanitising.
            hrefs = [a.get("href") for a in anchors]
            self.assertIn("https://example.com/a?b=1&c=2", hrefs)
            self.assertIn("docs/guide.md", hrefs)


if __name__ == "__main__":
    unittest.main()
