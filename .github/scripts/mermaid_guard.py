#!/usr/bin/env python3
"""Enforce Mermaid diagrams as fenced source in Markdown, not as .mmd files.

    python3 .github/scripts/mermaid_guard.py .

This repo's contribution docs intentionally keep diagrams in markdown fences so they stay
reviewable in GitHub without generated artifacts. A `.mmd` file or an empty Mermaid block is a
signal that a diagram drifted out of the source-of-truth path.
"""

from __future__ import annotations

import pathlib
import sys

SKIP_DIRS = {".git", ".terraform", "__pycache__", "node_modules", ".venv"}


def markdown_files(root: pathlib.Path):
    for path in sorted(root.rglob("*.md")):
        if SKIP_DIRS.isdisjoint(path.parts):
            yield path


def mermaid_blocks(path: pathlib.Path):
    in_fence = False
    fence_lang = ""
    body = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if in_fence:
                if fence_lang == "mermaid" and not any(part.strip() for part in body):
                    yield lineno, "empty mermaid block"
                in_fence = False
                fence_lang = ""
                body = []
            else:
                fence_lang = stripped[3:].strip().lower()
                in_fence = True
                body = []
            continue
        if in_fence and fence_lang == "mermaid":
            body.append(line)


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    errors = []

    for path in sorted(root.rglob("*.mmd")):
        if SKIP_DIRS.isdisjoint(path.parts):
            errors.append(f"MMD_FILE {path.relative_to(root)}")

    checked = 0
    for path in markdown_files(root):
        checked += 1
        for lineno, issue in mermaid_blocks(path):
            errors.append(f"MERMAID {path.relative_to(root)}:{lineno} {issue}")

    if errors:
        for error in errors:
            print(error)
        print(f"\n{len(errors)} mermaid/diagram guard violation(s) across {checked} markdown files")
        return 1

    print(f"{checked} markdown files checked; no .mmd diagrams; mermaid blocks are non-empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
