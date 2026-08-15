#!/usr/bin/env python3
"""Check every relative markdown link in the repository resolves to a file that exists.

    python3 .github/scripts/linkcheck.py .

Exits non-zero, listing file, line, and target, if any link is broken.

Standard library only, like every other check here — no linkchecker package, no network. It
only tests *relative* links, which is deliberate: external URLs go stale for reasons nobody
in this repository controls, and a CI job that fails because someone else's blog moved is a
job that gets disabled. Round one's REPO-AUDIT Task 12 was two broken relative links to a
workflow that had been renamed, and that is exactly the class this catches.

Two things a naive implementation gets wrong. Both were established by writing one: it
reported 34 broken links across this repository, and every single one was a false positive.

**Fenced code blocks.** REPO-AUDIT.md and both plan documents quote other files' markdown —
including their relative links — inside triple-backtick fences. Those links resolve against
the file being quoted, not the file doing the quoting, so checking them is meaningless. Fence
state has to be tracked and everything inside skipped.

**Fragment suffixes.** `ARCHITECTURE.md#6--what-terraform-builds` points at a file that
exists. Testing the whole string as a path fails. Split on `#` and test the left half.

Whether the anchor itself resolves is a harder question — it means parsing every heading in
the target and reproducing GitHub's slug algorithm — and is deliberately not attempted. A
check that is right about a narrow thing beats one that is approximately right about a wide
one.
"""

import pathlib
import re
import sys

# Markdown inline links: [text](target). Reference-style links and bare autolinks are not
# matched, and are not used in this repository.
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

SKIP_DIRS = {".git", "node_modules", ".terraform", "__pycache__"}

# Checked with startswith, so anything with a scheme or a pure anchor is left alone.
EXTERNAL = ("http://", "https://", "mailto:", "#", "tel:")


def markdown_files(root):
    for path in sorted(root.rglob("*.md")):
        if SKIP_DIRS.isdisjoint(path.parts):
            yield path


def broken_links(path, root):
    """Yield (lineno, target) for each relative link in `path` that does not resolve."""
    in_fence = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        # Both ``` and ~~~ open a fence. Toggling on the marker alone is enough here: a
        # closing fence carries no info language, and an opening one may.
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for target in LINK.findall(line):
            target = target.strip()
            if target.startswith(EXTERNAL):
                continue
            # Strip a #fragment, and a "title" if one is present.
            path_part = target.split("#", 1)[0].split(" ", 1)[0]
            if not path_part:
                continue
            if not (path.parent / path_part).exists():
                yield lineno, target


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")

    failures = []
    checked = 0
    for path in markdown_files(root):
        checked += 1
        for lineno, target in broken_links(path, root):
            failures.append((path.relative_to(root), lineno, target))

    for relative, lineno, target in failures:
        print(f"BROKEN {relative}:{lineno} -> {target}")

    if failures:
        print(f"\n{len(failures)} broken relative link(s) across {checked} markdown files")
        return 1
    print(f"{checked} markdown files checked, 0 broken relative links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
