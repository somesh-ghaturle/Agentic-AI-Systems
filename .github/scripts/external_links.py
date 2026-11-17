#!/usr/bin/env python3
"""Report external links in the markdown that are dead.

    python3 .github/scripts/external_links.py .

Exits non-zero listing file, line, URL and reason for each dead link.

This is the half `linkcheck.py` deliberately leaves out. External URLs go stale for reasons
nobody here controls, so this never runs on a pull request: `external-links.yml` runs it weekly
and opens an issue, which is a reminder and not a gate. The README carried a link to the wrong
OWASP project for months because nothing looked.

Only a definite answer counts as dead: 404, 410, or a host that does not resolve. A 403, a 429
or a timeout is a site declining a script, not a missing page, and reporting those would train
whoever reads the issue to close it unread.

Standard library only. It needs the network, which is why it is not a check.
"""

import pathlib
import re
import socket
import sys
import urllib.error
import urllib.request

URL = re.compile(r"\]\((https?://[^)\s]+)\)")
SKIP_DIRS = {".git", ".terraform", "__pycache__", "node_modules", ".venv", "venv"}
DEAD_STATUS = {404, 410}


def external_links(text):
    """Yield (lineno, url) for each external markdown link outside a fenced code block."""
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence:
            for url in URL.findall(line):
                yield lineno, url.split("#", 1)[0]


def verdict(url, timeout=15):
    """A reason string if `url` is definitely dead, else None."""
    request = urllib.request.Request(url, headers={"User-Agent": "link-check"})
    try:
        urllib.request.urlopen(request, timeout=timeout).close()
    except urllib.error.HTTPError as error:
        return f"HTTP {error.code}" if error.code in DEAD_STATUS else None
    except urllib.error.URLError as error:
        return "host does not resolve" if isinstance(error.reason, socket.gaierror) else None
    except (OSError, ValueError):
        return None
    return None


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    seen, dead = {}, []
    for path in sorted(root.rglob("*.md")):
        if not SKIP_DIRS.isdisjoint(path.parts):
            continue
        for lineno, url in external_links(path.read_text(encoding="utf-8")):
            if url not in seen:
                seen[url] = verdict(url)
            if seen[url]:
                dead.append(f"DEAD {path.relative_to(root)}:{lineno} -> {url} ({seen[url]})")
    print("\n".join(dead) if dead else f"{len(seen)} external links checked, none dead")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
