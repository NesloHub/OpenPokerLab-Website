"""Configuration for the daily article generator.

The generator picks a strategy topic (see topics.py), gathers research material
from the web and asks an LLM to write an original article about it. Add or edit
topics in topics.py; tune the research behaviour here.
"""

# A polite User-Agent. Some sites reject the default of the HTTP library.
USER_AGENT = "OpenPokerLabBot/1.0 (+https://openpokerlab.org)"

# --- research behaviour ----------------------------------------------------
# How many search results to consider, and how many pages to actually fetch and
# keep as source material for the article.
RESULTS_PER_TOPIC = 8
MAX_PAGES = 5

# Maximum number of pages kept from a single domain, so a search that returns
# mostly one site (e.g. Reddit) still spreads across a few viewpoints.
MAX_PER_DOMAIN = 3

# Subreddits used by the keyless Reddit search fallback.
REDDIT_SUBS = ["poker", "Poker_Theory"]

# Maximum characters of extracted page text kept per source. Lower = smaller
# prompt (cheaper), higher = more material for the model to work from.
PAGE_CHARS = 2500

# Pages that always belong in sitemap.xml, as (path, priority, lastmod).
# Articles are added on top of these on every run.
STATIC_PAGES = [
    ("", "1.0", "2026-09-26"),
    ("bankroll.html", "0.7", "2026-09-26"),
    ("beginner.html", "0.7", "2026-09-26"),
    ("calculator.html", "0.7", "2026-09-26"),
    ("content.html", "0.7", "2026-09-26"),
    ("equity-lab.html", "0.9", "2026-09-26"),
    ("glossary.html", "0.7", "2026-09-26"),
    ("notemanager.html", "0.7", "2026-09-26"),
    ("pokerlab-rng.html", "0.9", "2026-09-26"),
    ("pokervision.html", "0.9", "2026-09-26"),
    ("range-maker.html", "0.7", "2026-09-26"),
    ("ranges.html", "0.7", "2026-09-26"),
    ("sites.html", "0.7", "2026-09-26"),
    ("software.html", "0.9", "2026-09-26"),
    ("strategy.html", "0.7", "2026-09-26"),
]
