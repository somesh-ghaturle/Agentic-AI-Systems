"""Tests the chapter/example pairing guard: each check fires on the drift it names.

    python3 -m unittest tests.test_pairing -v

pairing.py had no suite (task 89). Its three checks were each mutation-tested once, by hand,
when they were written (tasks 72, 73 and 74), and nothing re-ran those mutations afterwards.
Each test here builds a minimal repository that passes, breaks one thing, and asserts that
exact failure.
"""

import importlib.util
import pathlib
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "pairing.py"

_spec = importlib.util.spec_from_file_location("pairing", SCRIPT)
pairing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pairing)

CHAPTERS = {  # chapter -> (file, the example that is its counterpart)
    "Context": ("CONTEXT-ENGINEERING.md", "ctx-ex"),
    "Harness": ("HARNESS-ENGINEERING.md", "har-ex"),
    "Evaluation": ("EVALUATION-ENGINEERING.md", "eva-ex"),
    "Environment": ("ENVIRONMENT-ENGINEERING.md", "env-ex"),
}
UNPAIRED = "free-ex"  # an example no chapter claims, as half the real ones are


def build(root):
    arch = root / "docs" / "agentic-system-architecture"
    arch.mkdir(parents=True)
    rows, index = [], []
    for chapter, (filename, example) in CHAPTERS.items():
        (arch / filename).write_text(
            f"# {chapter}\n\nRunnable counterpart: "
            f"[{example}](../../examples/{example}/README.md).\n\nBody.\n"
        )
        rows.append(f"| [{chapter}](docs/agentic-system-architecture/{filename}) | `{example}` |")
    for example in [e for _, e in CHAPTERS.values()] + [UNPAIRED]:
        chapter_file = next((f for f, e in CHAPTERS.values() if e == example), None)
        backlink = (f"\n[the chapter](../../docs/agentic-system-architecture/{chapter_file})\n"
                    if chapter_file else "")
        d = root / "examples" / example
        d.mkdir(parents=True)
        (d / "README.md").write_text(f"# {example}\n\n## What this is not\n\nNot much.\n{backlink}")
        index.append(f"- [{example}](examples/{example}/README.md) — what it shows")
    table = "| Chapter | Counterpart |\n|---|---|\n" + "\n".join(rows) + "\n"
    (root / "ROADMAP.md").write_text(table)
    (root / "README.md").write_text("## Runnable examples\n\n" + "\n".join(index) + "\n")


class PairingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        build(self.root)

    def result(self):
        import contextlib  # noqa: PLC0415
        import io  # noqa: PLC0415

        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = pairing.main(self.root)
        return code, out.getvalue()

    def edit(self, rel, old, new):
        path = self.root / rel
        text = path.read_text()
        self.assertIn(old, text, f"fixture edit anchor missing in {rel}")
        path.write_text(text.replace(old, new, 1))

    def assertFails(self, needle):
        code, out = self.result()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)


class TestTheFixture(PairingTest):
    def test_the_fixture_passes(self):
        code, out = self.result()
        self.assertEqual(code, 0, out)


class TestChapterToExample(PairingTest):
    def test_a_chapter_with_no_counterparts_line(self):
        self.edit("docs/agentic-system-architecture/HARNESS-ENGINEERING.md",
                  "Runnable counterpart:", "Counterpart, informally:")
        self.assertFails("HARNESS-ENGINEERING.md: no 'Runnable counterpart(s):' line found")

    def test_a_chapter_naming_an_example_that_does_not_exist(self):
        self.edit("docs/agentic-system-architecture/CONTEXT-ENGINEERING.md",
                  "examples/ctx-ex/README.md", "examples/renamed-ex/README.md")
        self.assertFails("names examples/renamed-ex/, which does not exist")

    def test_an_example_that_does_not_link_back(self):
        self.edit("examples/eva-ex/README.md",
                  "agentic-system-architecture/EVALUATION-ENGINEERING.md", "elsewhere.md")
        self.assertFails(
            "examples/eva-ex/README.md: does not link back to EVALUATION-ENGINEERING.md"
        )

    def test_a_filename_used_as_link_label_is_not_a_backlink(self):
        """The mutation the task 72 author first missed: a label is not a target."""
        self.edit("examples/eva-ex/README.md",
                  "[the chapter](../../docs/agentic-system-architecture/EVALUATION-ENGINEERING.md)",
                  "[EVALUATION-ENGINEERING.md](elsewhere.md)")
        self.assertFails("does not link back to EVALUATION-ENGINEERING.md")


class TestTheRoadmapTable(PairingTest):
    def test_a_row_that_omits_a_counterpart(self):
        self.edit("ROADMAP.md", "| `env-ex` |", "| none |")
        self.assertFails(
            "Environment row disagrees with ENVIRONMENT-ENGINEERING.md -- table omits env-ex"
        )

    def test_a_row_that_adds_one_the_chapter_does_not_name(self):
        self.edit("ROADMAP.md", "| `ctx-ex` |", "| `ctx-ex`, `free-ex` |")
        self.assertFails("table adds free-ex")

    def test_a_missing_row(self):
        self.edit("ROADMAP.md", "| [Harness]", "| [Harnesses]")
        self.assertFails("the chapter/counterpart table has no Harness row")


class TestEveryExampleIsFindableAndLimited(PairingTest):
    def test_an_example_missing_from_the_readme_index(self):
        entry = f"- [{UNPAIRED}](examples/{UNPAIRED}/README.md) — what it shows\n"
        self.edit("README.md", entry, "")
        self.assertFails(
            f"examples/{UNPAIRED}/ is in the tree but not in the 'Runnable examples' index"
        )

    def test_an_example_without_a_what_this_is_not_section(self):
        self.edit(f"examples/{UNPAIRED}/README.md", "## What this is not", "## Limits")
        self.assertFails(f"examples/{UNPAIRED}/README.md: no '## What this is not' section")

    def test_a_demoted_heading_does_not_count(self):
        self.edit(f"examples/{UNPAIRED}/README.md", "## What this is not", "What this is not")
        self.assertFails("no '## What this is not' section")

    def test_each_accepted_heading_spelling_passes(self):
        headings = ("What this example is not", "What this does not teach", "What is simplified")
        for heading in headings:
            with self.subTest(heading=heading):
                path = self.root / "examples" / UNPAIRED / "README.md"
                path.write_text(f"# x\n\n## {heading}\n\nText.\n")
                self.assertEqual(self.result()[0], 0)


class TestTheRealTree(unittest.TestCase):
    def test_the_repository_passes(self):
        import contextlib  # noqa: PLC0415
        import io  # noqa: PLC0415

        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pairing.main(REPO), 0, out.getvalue())


if __name__ == "__main__":
    unittest.main()
