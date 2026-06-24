import re

from .models import Item

_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_HEADER = re.compile(r"^###\s+(.*)$")
_IMG = re.compile(r"<img[^>]*>")
_ICONS = {"💬", "🔥"}


def _clean_source(raw: str) -> str:
    raw = _IMG.sub("", raw)
    return raw.replace("🍵", "").strip()


def parse_digest(markdown: str) -> list[Item]:
    items: list[Item] = []
    source = "Inconnu"  # fallback if a link appears before any feed header
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            continue
        header = _HEADER.match(line)
        if header:
            source = _clean_source(header.group(1))
            continue
        links = _LINK.findall(line)
        if not links:
            continue
        hot = False
        if len(links) >= 2 and links[0][0].strip() in _ICONS:
            hot = links[0][0].strip() == "🔥"
            title, url = links[1][0].strip(), links[1][1].strip()
        else:
            title, url = links[0][0].strip(), links[0][1].strip()
        if not title or not url:
            continue
        items.append(Item(title=title, url=url, source=source, hot=hot))
    return items
