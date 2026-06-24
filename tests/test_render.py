from veilleur.models import Connection, Item
from veilleur.render import render_note


def test_frontmatter_and_header():
    out = render_note([], "2026-06-23", 0)
    assert out.startswith("---\ntype: veille\nstatus: ⏳\ndate: 2026-06-23\n")
    assert "tags:\n  - veille\n" in out
    assert "# 📡 Veille — 2026-06-23" in out
    assert "0 articles retenus sur 0 analysés." in out


def test_item_block_with_connection():
    it = Item(title="Rust internals", url="https://x", source="Hacker News: Best",
              hot=True, score=9, tags=["rust", "async"],
              summary="Un résumé.", why="Pour approfondir async.",
              connections=[Connection("Ma note", "même thème")])
    out = render_note([it], "2026-06-23", 5)
    assert "1 articles retenus sur 5 analysés." in out
    assert "## [Rust internals](https://x)" in out
    assert "**Source :** Hacker News: Best · 🔥 · **Score :** 9/10" in out
    assert "**Tags :** rust, async" in out
    assert "Un résumé." in out
    assert "**Pourquoi pour toi :** Pour approfondir async." in out
    assert "### 🔗 Connexions" in out
    assert "- [[Ma note]] — même thème" in out


def test_no_connection_emits_empty_wikilink():
    it = Item(title="T", url="u", source="Blog", score=7, summary="s", why="w")
    out = render_note([it], "2026-06-23", 1)
    assert "- [[ ]]" in out
    assert "🔥" not in out  # not hot => no fire


def test_enrich_failed_shows_notice():
    it = Item(title="T", url="u", source="Blog", score=7, enrich_failed=True)
    out = render_note([it], "2026-06-23", 1)
    assert "Résumé indisponible" in out
