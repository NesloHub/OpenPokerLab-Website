"""Offline self-test of the render pipeline (no network, no LLM).

Run:  python scripts/selftest.py
It stubs feedparser/requests so it can import generate_article without the
third-party packages installed, then rebuilds articles.html + sitemap.xml and
renders a sample article to scripts/_sample.html for inspection.
"""
import sys
import types
from pathlib import Path

# --- stub the third-party modules so the import works offline -------------
feedparser = types.ModuleType("feedparser")
feedparser.parse = lambda *args, **kwargs: None
sys.modules["feedparser"] = feedparser

requests = types.ModuleType("requests")
requests.post = lambda *args, **kwargs: None
sys.modules["requests"] = requests

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import generate_article as g  # noqa: E402

g.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

# Rebuild the index + sitemap from the (empty) manifest.
g.write_index([])
g.write_sitemap([])

# Render a sample article page and check no placeholders are left behind.
page = g.render_page(
    BASE="../",
    TITLE="Sample Title",
    DESC="Sample description.",
    CANONICAL="https://openpokerlab.org/articles/_sample.html",
    OG_TYPE="article",
    HEAD_EXTRA=g.ARTICLE_HEAD_EXTRA,
    CONTENT=g.build_article_content(
        "Sample Title", "May 10, 2026", "<p>Body</p>", '                <li><a href="x">x</a></li>'
    ),
)
(SCRIPT_DIR / "_sample.html").write_text(page, encoding="utf-8")

leftovers = [t for t in ("{{TITLE}}", "{{CONTENT}}", "{{BASE}}") if t in page]
print("sample bytes:", len(page))
print("leftover placeholders:", leftovers or "none")
print("slugify:", g.slugify("Poker Player Wins $1,000,000!"))
print("OK")
