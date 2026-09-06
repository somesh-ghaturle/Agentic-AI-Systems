#!/usr/bin/env python3
"""Replace the Nth mermaid block in a markdown file with its rendered GIF,
keeping the mermaid source collapsed underneath for diff history.

    python3 embed.py <file.md> <block-index> <gif-slug> "<alt text>"

Idempotent: a block already wrapped in <details> is left alone.
"""
import os
import re
import sys

DETAILS = "<details>\n<summary>Mermaid source (kept for diff history)</summary>\n\n"


def main(path, index, slug, alt):
    src = open(path).read()
    blocks = list(re.finditer(r'^```mermaid\n.*?^```\n', src, re.S | re.M))
    if index >= len(blocks):
        sys.exit(f"{path}: no mermaid block {index} (found {len(blocks)})")
    b = blocks[index]

    # Already converted? The wrapper opens immediately before the fence.
    if src[:b.start()].rstrip().endswith("<summary>Mermaid source (kept for diff history)</summary>"):
        print(f"{path} #{index}: already embedded, skipped")
        return

    rel = os.path.relpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "diagrams", "gif", slug + ".gif"),
        os.path.dirname(os.path.abspath(path)),
    )
    gif = os.path.join(os.path.dirname(os.path.abspath(path)), rel)
    if not os.path.exists(gif):
        sys.exit(f"{path}: gif not found at {gif}")

    new = f"![{alt}]({rel})\n\n{DETAILS}{b.group(0)}\n</details>\n"
    open(path, "w").write(src[:b.start()] + new + src[b.end():])
    print(f"{path} #{index}: embedded {slug}.gif")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
