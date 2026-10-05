#!/usr/bin/env python3
"""Generate one original poker article per run and publish it to the static site.

Pipeline:
  1. Pick the next strategy topic from topics.py (tracked in articles/state.json).
  2. Gather research material for that topic: search the web, fetch the top
     results and extract the readable text of each page.
  3. Ask an LLM (DeepSeek by default) to write an original, in-depth article
     about the topic, using the material only as background.
  4. Render the article with scripts/layout.html, update articles/manifest.json,
     rebuild articles.html and regenerate sitemap.xml.

Designed for GitHub Actions: keys are read from the environment, and the run
exits successfully when there is nothing to do.

Environment variables:
  LLM_API_KEY     (required) e.g. a DeepSeek key
  LLM_BASE_URL    (optional) default https://api.deepseek.com
  LLM_MODEL       (optional) default deepseek-chat
  SEARCH_API_KEY  (optional) enables a real search API (Brave/Tavily/Serper)
  SEARCH_PROVIDER (optional) brave | tavily | serper (default: duckduckgo)
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import time
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from sources import (MAX_PAGES, MAX_PER_DOMAIN, PAGE_CHARS, REDDIT_SUBS,
                     RESULTS_PER_TOPIC, STATIC_PAGES, USER_AGENT)
from topics import TOPICS

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
ARTICLES_DIR = ROOT / "articles"
LAYOUT_FILE = SCRIPT_DIR / "layout.html"
STATE_FILE = ARTICLES_DIR / "state.json"
MANIFEST_FILE = ARTICLES_DIR / "manifest.json"
INDEX_FILE = ROOT / "articles.html"
SITEMAP_FILE = ROOT / "sitemap.xml"

SITE_URL = "https://openpokerlab.org"

LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").strip() or "https://api.deepseek.com"
LLM_MODEL = os.environ.get("LLM_MODEL", "").strip() or "deepseek-chat"
SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY", "").strip()
SEARCH_PROVIDER = os.environ.get("SEARCH_PROVIDER", "").strip().lower() or "duckduckgo"

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
    "You are the lead writer of OpenPokerLab, an educational poker website. You "
    "write original, accurate, in-depth strategy articles for microstakes cash-game "
    "players. You never plagiarise: you explain concepts in your own words and never "
    "copy sentences from your research material. You never invent statistics or "
    "quotes. You always answer with valid JSON."
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


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:70] or "poker-article"


def _site_name(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host[4:] if host.startswith("www.") else (host or url)
    except Exception:
        return url


def _resolve_ddg_url(href: str) -> str:
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if "uddg=" in href:
        params = parse_qs(urlparse(href).query)
        if params.get("uddg"):
            return params["uddg"][0]
    return href


def _search_duckduckgo(query: str, limit: int):
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for anchor in soup.select("a.result__a"):
        url = _resolve_ddg_url(anchor.get("href", ""))
        title = anchor.get_text(" ", strip=True)
        if url and title:
            results.append({"title": title, "url": url})
        if len(results) >= limit:
            break
    return results


def _search_brave(query, limit, api_key):
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": limit},
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        timeout=30,
    )
    response.raise_for_status()
    items = (response.json().get("web") or {}).get("results", [])[:limit]
    return [{"title": i.get("title", ""), "url": i.get("url", "")} for i in items if i.get("url")]


def _search_tavily(query, limit, api_key):
    response = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": api_key, "query": query, "max_results": limit},
        timeout=60,
    )
    response.raise_for_status()
    items = response.json().get("results", [])[:limit]
    return [{"title": i.get("title", ""), "url": i.get("url", "")} for i in items if i.get("url")]


def _search_serper(query, limit, api_key):
    response = requests.post(
        "https://google.serper.dev/search",
        json={"q": query, "num": limit},
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    items = response.json().get("organic", [])[:limit]
    return [{"title": i.get("title", ""), "url": i.get("link", "")} for i in items if i.get("link")]


def _search_reddit(query: str, limit: int):
    """Keyless fallback: Reddit's public search feed, restricted to poker subs."""
    results = []
    seen = set()
    per_sub = max(3, limit // max(1, len(REDDIT_SUBS)))
    for sub in REDDIT_SUBS:
        try:
            response = requests.get(
                f"https://www.reddit.com/r/{sub}/search.rss",
                params={"q": query, "restrict_sr": 1, "sort": "relevance", "limit": per_sub},
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except Exception as exc:
            log(f"reddit /r/{sub} search failed: {exc}")
            continue
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns):
            link_node = entry.find("a:link", ns)
            url = link_node.get("href") if link_node is not None else ""
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            if not url or "/comments/" not in url or url in seen:
                continue
            seen.add(url)
            results.append({"title": title or url, "url": url})
            if len(results) >= limit:
                return results
        time.sleep(1)
    return results


def web_search(query: str):
    """Find candidate pages for a query, preferring a configured search API."""
    if SEARCH_API_KEY and SEARCH_PROVIDER in ("brave", "tavily", "serper"):
        try:
            if SEARCH_PROVIDER == "brave":
                return _search_brave(query, RESULTS_PER_TOPIC, SEARCH_API_KEY)
            if SEARCH_PROVIDER == "tavily":
                return _search_tavily(query, RESULTS_PER_TOPIC, SEARCH_API_KEY)
            if SEARCH_PROVIDER == "serper":
                return _search_serper(query, RESULTS_PER_TOPIC, SEARCH_API_KEY)
        except Exception as exc:
            log(f"search provider {SEARCH_PROVIDER} failed: {exc} - falling back to duckduckgo")
    try:
        results = _search_reddit(query, RESULTS_PER_TOPIC)
        if results:
            log(f"reddit search returned {len(results)} results")
            return results
    except Exception as exc:
        log(f"reddit search failed: {exc}")
    try:
        return _search_duckduckgo(query, RESULTS_PER_TOPIC)
    except Exception as exc:
        log(f"duckduckgo search failed: {exc}")
        return []


def fetch_page_text(url: str) -> str:
    """Fetch a page and return its readable text (or '' when unusable)."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        if "html" not in response.headers.get("Content-Type", "").lower():
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
            tag.decompose()
        container = soup.find("article") or soup.find("main") or soup
        return re.sub(r"\s+", " ", container.get_text(" ", strip=True)).strip()
    except Exception as exc:
        log(f"skip page {url}: {exc}")
        return ""


def gather_research(topic):
    """Search for a topic and return usable sources with extracted text."""
    results = web_search(topic["query"])
    log(f"search returned {len(results)} candidate pages")
    sources = []
    seen_urls = set()
    per_site = {}
    for result in results:
        url = result["url"]
        site = _site_name(url)
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        text = fetch_page_text(url)
        if len(text) < 400:
            continue
        # cap pages per domain so no single site dominates the article
        if per_site.get(site, 0) >= MAX_PER_DOMAIN:
            continue
        per_site[site] = per_site.get(site, 0) + 1
        sources.append({
            "name": site,
            "title": result.get("title") or site,
            "url": url,
            "excerpt": text[:PAGE_CHARS],
        })
        if len(sources) >= MAX_PAGES:
            break
    return sources


def pick_topic(used_topics):
    for topic in TOPICS:
        if topic["title"] not in used_topics:
            return topic
    return None


def build_prompt(topic, sources) -> str:
    blocks = []
    for src in sources:
        blocks.append(
            f"- Source: {src['name']} ({src['url']})\n"
            f"  Title: {src['title']}\n"
            f"  Content: {src['excerpt']}"
        )
    joined = "\n\n".join(blocks)
    return (
        f"Topic: {topic['title']}\n"
        f"Angle: {topic.get('angle', '')}\n\n"
        "Below is research material collected from several poker websites. Treat it "
        "as background knowledge only.\n\n"
        f"{joined}\n\n"
        "Write ONE original, in-depth educational strategy article in English about "
        "the topic above, aimed at microstakes cash-game players. Rules:\n"
        "- Explain everything in your own words and synthesise across the sources; "
        "never copy sentences or phrases from the material.\n"
        "- Do not invent statistics, solver numbers or quotes, and do not mention "
        "the source websites in the body text.\n"
        "- 900-1300 words with a real structure: a short intro, 3-6 sections with "
        "<h2>, concrete examples, and a 'Key takeaways' bullet list at the end.\n"
        "- Use HTML with <h2>, <h3>, <p>, <ul>/<li> only (no <html>, <head>, "
        "<body> or <h1>).\n"
        "- Answer with JSON only, using the keys: title, description, slug, "
        "body_html, sources. \"sources\" is a list of {\"name\", \"url\"} objects "
        "for the pages you actually used."
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
    state = load_json(STATE_FILE, {"used_topics": []})
    used_topics = set(state.get("used_topics", []))
    manifest = load_json(MANIFEST_FILE, [])

    topic = pick_topic(used_topics)
    if topic is None:
        log("all topics covered - add more in scripts/topics.py")
        return 0
    log(f"topic: {topic['title']}")

    sources = gather_research(topic)
    log(f"gathered {len(sources)} usable sources")
    if not sources:
        log("WARNING: no research material found - search may be blocked or offline")
        return 0

    article = call_llm(build_prompt(topic, sources))
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
        name = (src.get("name") or _site_name(url)).strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            source_entries.append((name, url))
    if not source_entries:
        for src in sources:
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                source_entries.append((src["name"], src["url"]))

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

    used_topics.add(topic["title"])
    save_json(STATE_FILE, {"used_topics": sorted(used_topics)})

    write_index(manifest)
    write_sitemap(manifest)
    log(f"published articles/{filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
