#!/usr/bin/env python3
"""Generate one original poker article per run and publish it to the static site.

Pipeline:
  1. Collect fresh items from the RSS/Atom feeds listed in sources.py.
  2. Skip items already covered (tracked in articles/state.json).
  3. Ask an LLM (DeepSeek by default) to write an original article based on
     those facts, linking back to the original sources.
  4. Render the article with scripts/layout.html, update articles/manifest.json,
     rebuild articles.html and regenerate sitemap.xml.

Designed for GitHub Actions: the API key is read from the environment, and the
run exits successfully without publishing anything when there is nothing new, so
a quiet day never shows up as a failed job.

Environment variables:
  LLM_API_KEY   (required) e.g. a DeepSeek key
  LLM_BASE_URL  (optional) default https://api.deepseek.com
  LLM_MODEL     (optional) default deepseek-chat
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
from pathlib import Path

import feedparser
import requests

from sources import RSS_FEEDS, USER_AGENT, STATIC_PAGES

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
ARTICLES_DIR = ROOT / "articles"
LAYOUT_FILE = SCRIPT_DIR / "layout.html"
STATE_FILE = ARTICLES_DIR / "state.json"
MANIFEST_FILE = ARTICLES_DIR / "manifest.json"
INDEX_FILE = ROOT / "articles.html"
SITEMAP_FILE = ROOT / "sitemap.xml"

SITE_URL = "https://openpokerlab.org"
MAX_ITEMS = 8          # how many fresh items to send to the model
MAX_STATE_LINKS = 800  # how many already-covered links to remember

LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").strip() or "https://api.deepseek.com"
LLM_MODEL = os.environ.get("LLM_MODEL", "").strip() or "deepseek-chat"

ARTICLE_HEAD_EXTRA = """    <style>
        .article-main { max-width: 780px; margin: 0 auto; padding: 40px 20px 80px; }
        .article-main .page-header { text-align: center; margin-bottom: 26px; }
        .article-body h2 { margin-top: 34px; }
        .article-body h3 { margin-top: 26px; }
        .article-body p { margin: 14px 0; }
        .article-body ul, .article-body ol { margin: 14px 0 14px 24px; }
        .article-body li { margin: 8px 0; }
        .article-meta { color: var(--dim); font-size: var(--fs-small); text-align: center; margin-top: 8px; }
        .article-sources { margin-top: 40px; padding: 18px 22px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }
        .article-sources h3 { margin-top: 0; }
        .article-sources ul { margin: 10px 0 0 20px; }
        .article-sources li { margin: 6px 0; }
        .article-back { display: inline-block; margin-top: 30px; color: var(--accent); text-decoration: none; }
        .article-back:hover { text-decoration: underline; }
    </style>"""

INDEX_HEAD_EXTRA = """    <style>
        .articles-main { max-width: 1040px; margin: 0 auto; padding: 40px 20px 80px; }
        .articles-main .page-header { text-align: center; margin-bottom: 36px; }
        .article-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .article-card { display: block; padding: 22px 24px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); text-decoration: none; transition: border-color 0.2s ease, transform 0.2s ease; }
        .article-card:hover { border-color: var(--accent-line); transform: translateY(-2px); }
        .article-card h3 { margin: 10px 0 8px; font-size: 1.15rem; }
        .article-card p { margin: 0; color: var(--muted); font-size: var(--fs-small); }
        .article-card .tag { display: inline-block; font-size: var(--fs-tiny); letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent); }
        .article-empty { color: var(--dim); }
    </style>"""

SYSTEM_PROMPT = (
    "You are the editor of OpenPokerLab, an educational poker website for players "
    "who care about strategy and the poker ecosystem. You write concise, original, "
    "well-sourced articles. You never plagiarise: you summarise and add context in "
    "your own words. You always answer with valid JSON."
)


def log(message: str) -> None:
    print(f"[generate_article] {message}", flush=True)


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"WARNING: could not parse {path.name}, starting from scratch")
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:70] or "poker-article"


def collect_items():
    """Read every configured feed and return a flat list of news items."""
    items = []
    for feed in RSS_FEEDS:
        name, url = feed["name"], feed["url"]
        try:
            parsed = feedparser.parse(url, agent=USER_AGENT)
        except Exception as exc:  # network, DNS, TLS, ...
            log(f"skip {name}: {exc}")
            continue
        if getattr(parsed, "bozo", 0) and not parsed.entries:
            log(f"skip {name}: feed unavailable")
            continue
        for entry in parsed.entries[:10]:
            link = (entry.get("link") or "").strip()
            title = strip_html(entry.get("title", ""))
            if not link or not title:
                continue
            published = ""
            if entry.get("published_parsed"):
                published = dt.datetime(*entry.published_parsed[:6]).strftime("%b %d, %Y")
            items.append({
                "source": name,
                "title": title,
                "link": link,
                "summary": strip_html(entry.get("summary", ""))[:600],
                "published": published,
            })
    return items


def build_prompt(items) -> str:
    blocks = []
    for it in items:
        blocks.append(
            f"- Source: {it['source']}\n"
            f"  Title: {it['title']}\n"
            f"  Link: {it['link']}\n"
            f"  Excerpt: {it['summary']}"
        )
    joined = "\n".join(blocks)
    return (
        "Here are today's latest poker news items:\n\n"
        f"{joined}\n\n"
        "Write one original, well-structured article in English that ties these "
        "developments together for a poker audience. Rules:\n"
        "- Summarise and explain in your own words; never copy source sentences.\n"
        "- 600-800 words, using HTML with <h2>, <h3>, <p>, <ul>/<li> only "
        "(no <html>, <head>, <body> or <h1>).\n"
        "- Stay factual and neutral and never invent statistics or quotes.\n"
        "- Answer with JSON only, using the keys: title, description, slug, "
        "body_html, sources. \"sources\" is a list of {\"name\", \"url\"} objects "
        "pointing at the original links above."
    )


def call_llm(prompt: str) -> dict:
    if not LLM_API_KEY:
        raise SystemExit("LLM_API_KEY is not set (add it as a repository secret).")
    response = requests.post(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def render_page(**values) -> str:
    page = LAYOUT_FILE.read_text(encoding="utf-8")
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)
    return page


def build_article_content(title, date_str, body_html, sources_html) -> str:
    return (
        '    <main class="article-main">\n'
        '        <section class="page-header">\n'
        f'            <h1 class="elegant-title-small">{html.escape(title)}</h1>\n'
        f'            <p class="article-meta">Published {date_str} &middot; OpenPokerLab Editorial</p>\n'
        "        </section>\n\n"
        '        <article class="article-body">\n'
        f"{body_html}\n"
        "        </article>\n\n"
        '        <section class="article-sources">\n'
        "            <h3>Sources</h3>\n"
        "            <ul>\n"
        f"{sources_html}\n"
        "            </ul>\n"
        "        </section>\n\n"
        '        <a class="article-back" href="../articles.html">&larr; All articles</a>\n'
        "    </main>"
    )


def write_index(manifest) -> None:
    if manifest:
        cards = "\n".join(
            '                <a class="article-card" href="articles/{file}">\n'
            '                    <span class="tag">{date}</span>\n'
            "                    <h3>{title}</h3>\n"
            "                    <p>{desc}</p>\n"
            "                </a>".format(
                file=html.escape(entry["file"]),
                date=html.escape(entry.get("date_display", entry["date"])),
                title=html.escape(entry["title"]),
                desc=html.escape(entry.get("description", "")),
            )
            for entry in manifest
        )
    else:
        cards = '                <p class="article-empty">No articles yet. Check back soon.</p>'

    content = (
        '    <main class="articles-main">\n'
        '        <section class="page-header">\n'
        '            <h1 class="elegant-title-small">POKER <span class="title-highlight">ARTICLES</span></h1>\n'
        '            <p class="subtitle">Original poker news and analysis, written daily.</p>\n'
        "        </section>\n"
        '        <section class="article-grid">\n'
        f"{cards}\n"
        "        </section>\n"
        "    </main>"
    )

    page = render_page(
        BASE="",
        TITLE=html.escape("Poker Articles & Analysis"),
        DESC=html.escape("A daily feed of original poker news, strategy and analysis from OpenPokerLab."),
        CANONICAL=f"{SITE_URL}/articles.html",
        OG_TYPE="website",
        HEAD_EXTRA=INDEX_HEAD_EXTRA,
        CONTENT=content,
    )
    INDEX_FILE.write_text(page, encoding="utf-8")


def write_sitemap(manifest) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, priority, lastmod in STATIC_PAGES:
        loc = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
        lines += [
            "    <url>",
            f"        <loc>{loc}</loc>",
            f"        <lastmod>{lastmod}</lastmod>",
            f"        <priority>{priority}</priority>",
            "    </url>",
        ]
    today = dt.date.today().isoformat()
    lines += [
        "    <url>",
        f"        <loc>{SITE_URL}/articles.html</loc>",
        f"        <lastmod>{today}</lastmod>",
        "        <priority>0.8</priority>",
        "    </url>",
    ]
    for entry in manifest:
        lines += [
            "    <url>",
            f"        <loc>{SITE_URL}/articles/{entry['file']}</loc>",
            f"        <lastmod>{entry['date']}</lastmod>",
            "        <priority>0.6</priority>",
            "    </url>",
        ]
    lines.append("</urlset>")
    SITEMAP_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    state = load_json(STATE_FILE, {"used_links": []})
    used = set(state.get("used_links", []))
    manifest = load_json(MANIFEST_FILE, [])

    items = collect_items()
    fresh = [item for item in items if item["link"] not in used]
    log(f"collected {len(items)} items, {len(fresh)} new")
    if not fresh:
        log("nothing new to publish - done")
        return 0
    fresh = fresh[:MAX_ITEMS]

    article = call_llm(build_prompt(fresh))
    title = (article.get("title") or "").strip()
    description = (article.get("description") or "").strip()
    body_html = (article.get("body_html") or "").strip()
    slug = slugify(article.get("slug") or title)
    if not title or not body_html:
        log("ERROR: the model returned an incomplete article")
        return 1

    source_entries = []
    seen_urls = set()
    for src in article.get("sources", []) or []:
        url = (src.get("url") or "").strip()
        name = (src.get("name") or url).strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            source_entries.append((name, url))
    if not source_entries:
        for item in fresh:
            if item["link"] not in seen_urls:
                seen_urls.add(item["link"])
                source_entries.append((item["source"], item["link"]))

    sources_html = "\n".join(
        '                <li><a href="{}" target="_blank" rel="noopener noreferrer">{}</a></li>'.format(
            html.escape(url, quote=True), html.escape(name)
        )
        for name, url in source_entries
    )

    today = dt.date.today()
    iso = today.isoformat()
    date_str = today.strftime("%B %d, %Y")
    filename = f"{iso}-{slug}.html"
    canonical = f"{SITE_URL}/articles/{filename}"

    page = render_page(
        BASE="../",
        TITLE=html.escape(title),
        DESC=html.escape(description),
        CANONICAL=canonical,
        OG_TYPE="article",
        HEAD_EXTRA=ARTICLE_HEAD_EXTRA,
        CONTENT=build_article_content(title, date_str, body_html, sources_html),
    )
    (ARTICLES_DIR / filename).write_text(page, encoding="utf-8")

    manifest = [entry for entry in manifest if entry.get("file") != filename]
    manifest.insert(0, {
        "file": filename,
        "slug": slug,
        "title": title,
        "description": description,
        "date": iso,
        "date_display": date_str,
        "sources": [{"name": n, "url": u} for n, u in source_entries],
    })
    save_json(MANIFEST_FILE, manifest)

    for item in fresh:
        used.add(item["link"])
    save_json(STATE_FILE, {"used_links": list(used)[-MAX_STATE_LINKS:]})

    write_index(manifest)
    write_sitemap(manifest)
    log(f"published articles/{filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
