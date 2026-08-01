"""Build a static, htmx-boosted multipage site from this repo's Markdown docs.

Usage:
    uv run --with markdown python scripts/build_docs_site.py

Then serve docs-site/ over HTTP (htmx's boosted fetches don't work over
file://) and open index.html:
    python -m http.server --directory docs-site 8000
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

import markdown

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "docs-site"


@dataclass(frozen=True)
class Page:
    slug: str
    title: str
    source: Path
    group: str


PAGES = [
    Page("readme", "Overview", REPO_ROOT / "README.md", "Get started"),
    Page("user-guide", "Complete user guide", REPO_ROOT / "docs/user-guide.md", "Get started"),
    Page(
        "tutorial-01",
        "Tutorial 1 · Foundations",
        REPO_ROOT / "docs/tutorial/01_timesfm_intro.md",
        "Zero-to-master tutorial",
    ),
    Page(
        "tutorial-02",
        "Tutorial 2 · Local installation",
        REPO_ROOT / "docs/tutorial/02_local_installation.md",
        "Zero-to-master tutorial",
    ),
    Page(
        "tutorial-03",
        "Tutorial 3 · Data engineering",
        REPO_ROOT / "docs/tutorial/03_data_engineering.md",
        "Zero-to-master tutorial",
    ),
    Page(
        "tutorial-04",
        "Tutorial 4 · Forecasting mastery",
        REPO_ROOT / "docs/tutorial/04_forecasting_mastery.md",
        "Zero-to-master tutorial",
    ),
    Page("manual-datasets", "Manual datasets", REPO_ROOT / "docs/manual-datasets.md", "Reference"),
    Page(
        "threat-model",
        "Threat model",
        REPO_ROOT / "timesfm-forecasting-studio-threat-model.md",
        "Reference",
    ),
    Page("changelog", "Changelog", REPO_ROOT / "CHANGELOG.md", "Reference"),
    Page("contributing", "Contributing", REPO_ROOT / "CONTRIBUTING.md", "Community"),
    Page("security", "Security policy", REPO_ROOT / "SECURITY.md", "Community"),
    Page("support", "Support", REPO_ROOT / "SUPPORT.md", "Community"),
    Page("code-of-conduct", "Code of conduct", REPO_ROOT / "CODE_OF_CONDUCT.md", "Community"),
]

MERMAID_BLOCK = re.compile(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL
)
LINK_HREF = re.compile(r'href="([^"]+)"')
SOURCE_TO_SLUG = {page.source.resolve(): page.slug for page in PAGES}


def _rewrite_link(href: str, source_dir: Path) -> str:
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    path_part, _, fragment = href.partition("#")
    if not path_part:
        return href
    target = (source_dir / path_part).resolve()
    slug = SOURCE_TO_SLUG.get(target)
    if slug is None:
        return href
    return f"{slug}.html#{fragment}" if fragment else f"{slug}.html"

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · TimesFM Forecast Studio docs</title>
<link rel="stylesheet" href="style.css">
<script src="vendor/htmx.min.js"></script>
</head>
<body>
<div class="layout">
<nav id="sidebar" hx-boost="true" hx-target="#content" hx-select="#content" hx-swap="innerHTML" hx-push-url="true">
<div class="brand">TimesFM Forecast Studio<span>docs</span></div>
{nav}
</nav>
<main>
<div id="content">
{body}
</div>
</main>
</div>
<script src="vendor/mermaid.min.js"></script>
<script>
mermaid.initialize({{ startOnLoad: true, theme: "neutral" }});
document.body.addEventListener("htmx:afterSwap", function () {{
    mermaid.run({{ querySelector: "#content .mermaid" }});
}});
</script>
</body>
</html>
"""


def build_nav(active_slug: str) -> str:
    groups: dict[str, list[Page]] = {}
    for page in PAGES:
        groups.setdefault(page.group, []).append(page)
    parts = []
    for group, pages in groups.items():
        parts.append(f'<div class="nav-group"><h2>{html.escape(group)}</h2><ul>')
        for page in pages:
            css = ' class="active"' if page.slug == active_slug else ""
            parts.append(f'<li><a href="{page.slug}.html"{css}>{html.escape(page.title)}</a></li>')
        parts.append("</ul></div>")
    return "\n".join(parts)


def render_page(page: Page) -> str:
    text = page.source.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
    )

    def unwrap_mermaid(match: re.Match[str]) -> str:
        return f'<pre class="mermaid">{html.unescape(match.group(1))}</pre>'

    body = MERMAID_BLOCK.sub(unwrap_mermaid, body)
    source_dir = page.source.parent
    body = LINK_HREF.sub(lambda m: f'href="{_rewrite_link(m.group(1), source_dir)}"', body)
    return SHELL.format(title=page.title, nav=build_nav(page.slug), body=body)


def main() -> None:
    SITE_DIR.mkdir(exist_ok=True)
    for page in PAGES:
        html_out = render_page(page)
        (SITE_DIR / f"{page.slug}.html").write_text(html_out, encoding="utf-8")
    (SITE_DIR / "index.html").write_text(render_page(PAGES[0]), encoding="utf-8")
    print(f"Built {len(PAGES)} pages + index.html into {SITE_DIR}")


if __name__ == "__main__":
    main()
