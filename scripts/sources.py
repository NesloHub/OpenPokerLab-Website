"""Content sources for the daily article generator.

Only public RSS/Atom feeds are used. Add or remove entries here to change what
the generator reads. Every feed is best-effort: a source that is down, moved or
rate-limited is skipped so a single broken feed never breaks the whole run.
"""

# RSS / Atom feeds from poker news outlets and community sources.
# NOTE: feed URLs change over time. If a source stops returning items it is
# simply skipped, but it is worth verifying the list now and then.
RSS_FEEDS = [
    {"name": "PokerNews", "url": "https://www.pokernews.com/news.rss"},
    {"name": "CardPlayer", "url": "https://www.cardplayer.com/poker-news/rss"},
    {"name": "PokerStars Blog", "url": "https://www.pokerstars.com/blog/feed/"},
    {"name": "PokerStrategy", "url": "https://www.pokerstrategy.com/news/rss/"},
    {"name": "PokerListings", "url": "https://www.pokerlistings.com/feed"},
    {"name": "Pokerfuse", "url": "https://pokerfuse.com/feed/"},
    {"name": "Reddit r/poker", "url": "https://www.reddit.com/r/poker/top/.rss?t=day"},
    {"name": "Reddit r/poker (new)", "url": "https://www.reddit.com/r/poker/new/.rss"},
]

# A polite User-Agent. Reddit in particular rejects the library default.
USER_AGENT = "OpenPokerLabBot/1.0 (+https://openpokerlab.org)"

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
