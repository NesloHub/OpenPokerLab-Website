"""Offline self-test of the render pipeline (no network, no LLM).

Run:  python scripts/selftest.py
It stubs bs4/requests so it can import generate_article without the third-party
packages installed, then rebuilds articles.html + sitemap.xml and renders a
sample article to scripts/_sample.html for inspection.
"""
import sys
import types
from pathlib import Path

# --- stub the third-party modules so the import works offline -------------
bs4 = types.ModuleType("bs4")
bs4.BeautifulSoup = object
sys.modules["bs4"] = bs4

requests = types.ModuleType("requests")
requests.get = lambda *args, **kwargs: None
requests.post = lambda *args, **kwargs: None
sys.modules["requests"] = requests

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import generate_article as g  # noqa: E402

g.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

# Render a sample article page and check no placeholders are left behind.
# (This intentionally does NOT touch the real articles.html / sitemap.xml.)
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
