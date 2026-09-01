#!/usr/bin/env python3
"""Generate a static preview site for repository markdown docs.

    python3 .github/scripts/docs_preview.py . out/docs-preview

The script walks the repository, finds markdown files, and writes a small HTML preview for
each file. It is intentionally lightweight and dependency-free so it can run in GitHub Actions
without a documentation framework or added Python packages.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".terraform", "__pycache__", "node_modules", ".venv", "venv"}


def is_markdown_target(path: Path) -> bool:
    return path.suffix.lower() == ".md" and SKIP_DIRS.isdisjoint(path.parts)


def iter_markdown(root: Path):
    for path in sorted(root.rglob("*.md")):
        if is_markdown_target(path):
            yield path


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value.lower())
    value = re.sub(r"\s+", "-", value.strip())
    return value or "section"


def heading_text(line: str) -> str | None:
    m = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
    if not m:
        return None
    return m.group(2).strip()


def escape_text(value: str) -> str:
    return html.escape(value, quote=False)


def render_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    code_buffer: list[str] = []

    def flush_code():
        nonlocal in_code, code_buffer
        if in_code:
            code_html = html.escape("\n".join(code_buffer), quote=False)
            out.append(f"<pre><code>{code_html}</code></pre>")
            in_code = False
            code_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_code()
            in_code = not in_code
            continue
        if in_code:
            code_buffer.append(line)
            continue

        if not stripped:
            flush_code()
            if out and out[-1] != "<p></p>":
                out.append("<p></p>")
            continue

        heading = heading_text(line)
        if heading is not None:
            flush_code()
            level = len(re.match(r"^(#+)", line).group(1))
            out.append(f"<h{level}>{render_inline(heading)}</h{level}>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_code()
            if not out or out[-1] != "<ul>":
                out.append("<ul>")
            out.append(f"<li>{render_inline(stripped[2:])}</li>")
            continue

        if out and out[-1] == "<ul>":
            out.append("</ul>")

        if stripped.startswith("|") and "|" in stripped:
            flush_code()
            # Do not render markdown tables unless they are present; keep them as paragraphs.
            out.append(f"<p>{render_inline(stripped)}</p>")
            continue

        flush_code()
        out.append(f"<p>{render_inline(stripped)}</p>")

    flush_code()
    if out and out[-1] == "<ul>":
        out.append("</ul>")
    return "\n".join(out)


def html_document(title: str, body: str, nav_entries: str) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape_text(title)}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      margin: 0;
      background: #f5f7fb;
      color: #1e293b;
    }}
    .layout {{ display: flex; min-height: 100vh; }}
    nav {{
      width: 300px;
      background: #0f172a;
      color: #e2e8f0;
      padding: 1.5rem;
      box-sizing: border-box;
    }}
    nav h1 {{ font-size: 1.1rem; margin-top: 0; }}
    nav ul {{ list-style: none; padding: 0; margin: 0; }}
    nav li {{ margin: 0.3rem 0; }}
    nav a {{ color: #cbd5e1; text-decoration: none; }}
    nav a:hover {{ text-decoration: underline; }}
    main {{ flex: 1; padding: 2rem; max-width: 1000px; }}
    .content {{
      background: white;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    }}
    h1, h2, h3, h4 {{ color: #0f172a; }}
    code {{
      background: #eff6ff;
      border-radius: 4px;
      padding: 0.12rem 0.3rem;
    }}
    pre {{
      background: #0f172a;
      color: #e2e8f0;
      padding: 1rem;
      overflow-x: auto;
      border-radius: 8px;
    }}
    a {{ color: #0f766e; }}
    p {{ line-height: 1.6; }}
    li {{ margin: 0.35rem 0; }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <nav>
      <h1>Repository docs</h1>
      <ul>{nav_entries}</ul>
    </nav>
    <main>
      <div class=\"content\">{body}</div>
    </main>
  </div>
</body>
</html>
"""


def load_pages(root: Path):
    markdown_paths = list(iter_markdown(root))
    pages = []
    for path in markdown_paths:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        title = rel.name.replace(".md", "").replace("-", " ").title()
        for line in text.splitlines():
            heading = heading_text(line)
            if heading:
                title = heading
                break
        pages.append((rel, title, text))
    return pages


def build_site(root: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = load_pages(root)

    # Write pages.
    for rel, title, text in pages:
        target = out_dir / rel.with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        body_html = render_markdown(text)
        page_nav = "".join(
            (
                '<li><a href="'
                f"{page_rel.as_posix()}"
                f'">{escape_text(page_title)}</a></li>'
            )
            for page_rel, page_title, _ in pages
        )
        target.write_text(html_document(title, body_html, page_nav), encoding="utf-8")

    # Write index page.
    index_nav = "".join(
        (
            '<li><a href="'
            f"{rel.with_suffix('.html').as_posix()}"
            f'">{escape_text(title)}</a></li>'
        )
        for rel, title, _ in pages
    )
    index_body = (
        "<h1>Documentation preview</h1>"
        "<p>This preview is generated from the repository markdown files and is "
        "meant for quick review in pull requests.</p>"
    )
    index_html = html_document(
        "Documentation preview",
        index_body + "<ul>" + index_nav + "</ul>",
        index_nav,
    )
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")



def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "docs-preview").resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    build_site(root, out_dir)
    print(f"Generated docs preview in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
