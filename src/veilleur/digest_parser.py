"""Parser for matcha's markdown digest — the sole coupling point to matcha.

matcha writes one markdown file per day. Feed sections are ``###`` headers
(prefixed by a favicon ``<img>`` tag or the 🍵 emoji); each article is a
markdown link. Hacker News items additionally carry a leading icon link to the
discussion (``[💬 ](commentsURL)`` or ``[🔥 ](commentsURL)``), so for those the
real article is the *second* link and 🔥 marks a popular item (>=100 comments).

If matcha ever changes its output format, this module — and only this module —
needs updating (see ``tests/test_digest_parser.py`` and its fixture).
"""

import re

from .models import Item

# A markdown link: capture (text, url).
_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# A feed-section header line. matcha emits ``###`` only.
_HEADER = re.compile(r"^###\s+(.*)$")
# The favicon <img> tag matcha prefixes onto feed titles.
_IMG = re.compile(r"<img[^>]*>")
# Icons matcha uses on Hacker News items (comments link prefix).
_HN_ICONS = {"💬", "🔥"}


def _clean_source(raw_header: str) -> str:
    """Extract a clean feed name from a header line.

    Strips matcha's favicon ``<img>`` tag and the 🍵 fallback emoji.
    """
    without_img = _IMG.sub("", raw_header)
    return without_img.replace("🍵", "").strip()


def parse_digest(markdown: str) -> list[Item]:
    """Parse a matcha markdown digest into a list of items.

    Args:
        markdown: The full contents of matcha's daily digest file.

    Returns:
        One :class:`Item` per article, in document order, with ``title``,
        ``url``, ``source`` and ``hot`` populated. Header lines and lines
        without a markdown link are skipped.
    """
    items: list[Item] = []
    source = "Inconnu"  # fallback if a link appears before any feed header
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        header = _HEADER.match(line)
        if header:
            source = _clean_source(header.group(1))
            continue
        links = _LINK.findall(line)
        if not links:
            continue
        # Hacker News lines start with a comments-link icon; the article is the
        # second link. Everything else has the article as its only/first link.
        hot = False
        if len(links) >= 2 and links[0][0].strip() in _HN_ICONS:
            hot = links[0][0].strip() == "🔥"
            title, url = links[1][0].strip(), links[1][1].strip()
        else:
            title, url = links[0][0].strip(), links[0][1].strip()
        if not title or not url:
            continue
        items.append(Item(title=title, url=url, source=source, hot=hot))
    return items
