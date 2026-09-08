#!/usr/bin/env python3
"""Check that each architecture chapter and its runnable examples still agree.

    python3 .github/scripts/pairing.py .

Exits non-zero naming the chapter, the example, and which side of the pairing moved.

Why this exists. ROADMAP.md calls this pairing "the thing to protect" and says the highest-value
maintenance here is noticing when a chapter and its example stop agreeing -- then states the
pairing a second time, in its own table, where it promptly drifted from the chapters twice: the
Context row named an example the chapter did not, and the Environment row omitted one the chapter
did. Prose that says "keep these in step" is not a mechanism for keeping them in step.

WHAT THIS DOES NOT CHECK, said plainly because the obvious reading of the ROADMAP sentence is
stricter than what is enforceable: it does not require every example to belong to a chapter. Half
of them do not, and should not -- `rag-faiss` and `langchain-agent` demonstrate a framework,
`e2e-agent` exists as a cautionary counter-example, `hermes-dashboard` is an approval UX. Forcing
a chapter link onto those would produce a link that means nothing, which is the failure this file
is trying to prevent rather than a fix for it.

The direction it does check is the one that can silently rot: a chapter naming a counterpart that
has been renamed, deleted, or has quietly stopped pointing back.

The second check is the complement, and it is the one that covers the examples no chapter claims:
every example must at least be listed in README.md's "Runnable examples" index, with a line saying
what it shows. That index had drifted to seventeen of twenty-four -- every boundary example added
in the last stretch was missing from it, so the examples arguing the repository's central claim
were the ones a reader could not find.
"""

import pathlib
import re
import sys

CHAPTERS = {
    "Context": "CONTEXT-ENGINEERING.md",
    "Harness": "HARNESS-ENGINEERING.md",
    "Evaluation": "EVALUATION-ENGINEERING.md",
    "Environment": "ENVIRONMENT-ENGINEERING.md",
}

# "Runnable counterpart:" and "Runnable counterparts:" both occur, and the list runs to the
# next blank line -- ENVIRONMENT's spans five lines.
COUNTERPARTS = re.compile(r"^Runnable counterparts?:(.*?)(?=\n\n)", re.M | re.S)
EXAMPLE_LINK = re.compile(r"examples/([a-z0-9-]+)/README\.md")
ROADMAP_ROW = re.compile(r"^\| \[(\w+)\]\([^)]*\) \| (.+?) \|$", re.M)
BACKTICKED = re.compile(r"`([a-z0-9-]+)`")
INDEXED = re.compile(r"\(examples/([a-z0-9-]+)/README\.md\)")


def chapter_counterparts(root):
    """{chapter: {example, ...}} as each chapter itself declares it."""
    out = {}
    for name, filename in CHAPTERS.items():
        text = (root / "docs/agentic-system-architecture" / filename).read_text()
        m = COUNTERPARTS.search(text)
        out[name] = set(EXAMPLE_LINK.findall(m.group(1))) if m else set()
    return out


def roadmap_counterparts(root):
    """{chapter: {example, ...}} as ROADMAP.md's table restates it."""
    text = (root / "ROADMAP.md").read_text()
    return {
        chapter: set(BACKTICKED.findall(cell))
        for chapter, cell in ROADMAP_ROW.findall(text)
        if chapter in CHAPTERS
    }


def main(root):
    root = pathlib.Path(root).resolve()
    declared = chapter_counterparts(root)
    restated = roadmap_counterparts(root)
    failures = []

    for chapter, examples in sorted(declared.items()):
        if not examples:
            failures.append(
                f"{CHAPTERS[chapter]}: no 'Runnable counterpart(s):' line found -- a chapter with "
                f"no example drifts into assertion, which is the pairing this checks"
            )
            continue

        for example in sorted(examples):
            readme = root / "examples" / example / "README.md"
            if not readme.is_file():
                failures.append(f"{CHAPTERS[chapter]}: names examples/{example}/, "
                                f"which does not exist")
                continue
            # The link TARGET, not the filename anywhere in the text. A README that merely
            # mentions the chapter -- or uses its filename as a link label, which several do --
            # is not pointing back at it.
            if f"agentic-system-architecture/{CHAPTERS[chapter]}" not in readme.read_text():
                failures.append(
                    f"examples/{example}/README.md: does not link back to {CHAPTERS[chapter]}, "
                    f"which names it as a runnable counterpart"
                )

        if chapter not in restated:
            failures.append(f"ROADMAP.md: the chapter/counterpart table has no {chapter} row")
        elif restated[chapter] != examples:
            missing = sorted(examples - restated[chapter])
            extra = sorted(restated[chapter] - examples)
            detail = []
            if missing:
                detail.append(f"table omits {', '.join(missing)}")
            if extra:
                detail.append(f"table adds {', '.join(extra)}")
            failures.append(f"ROADMAP.md: {chapter} row disagrees with {CHAPTERS[chapter]} -- "
                            + "; ".join(detail))

    # Every example is findable, whether or not a chapter claims it. A directory with no
    # chapter and no index entry is not a decision, it is an omission -- which is how seven
    # of them, including four boundary examples, went unlisted.
    indexed = set(INDEXED.findall((root / "README.md").read_text()))
    for example in sorted(d.name for d in (root / "examples").iterdir() if d.is_dir()):
        if example not in indexed:
            failures.append(
                f"README.md: examples/{example}/ is in the tree but not in the "
                f"'Runnable examples' index -- add it with a line saying what it shows"
            )

    if failures:
        print("Chapters and their runnable counterparts disagree:\n")
        for f in failures:
            print(f"  {f}")
        return 1

    pairs = sum(len(v) for v in declared.values())
    print(f"{len(CHAPTERS)} chapters checked, {pairs} chapter/example pairings, "
          f"{len(indexed)} examples indexed; each example exists, links back, matches the "
          "ROADMAP table, and is findable from the README")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
