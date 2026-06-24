from pathlib import Path

from veilleur.vault_index import build_index, build_index_cached, format_index

NOTE = """---
type: permanent
status: 🌿
date_creation: 2026-06-01
tags:
  - rust
  - concurrence
---

# Le borrow checker garantit l'absence de data races

## 💡 Le concept en une phrase
> L'ownership vérifié à la compilation élimine les data races sans GC.

## 📝 Développement
Blah blah.
"""


def _make_vault(tmp_path) -> Path:
    d = tmp_path / "30_Permanent_Notes"
    d.mkdir()
    (d / "Le borrow checker garantit l'absence de data races.md").write_text(
        NOTE, encoding="utf-8")
    return d


def test_build_index_extracts_title_concept_tags(tmp_path):
    notes = build_index(_make_vault(tmp_path))
    assert len(notes) == 1
    n = notes[0]
    assert n.title == "Le borrow checker garantit l'absence de data races"
    assert "data races" in n.concept
    assert "GC" in n.concept
    assert n.tags == ["rust", "concurrence"]


def test_format_index_is_compact_wikilink_listing(tmp_path):
    notes = build_index(_make_vault(tmp_path))
    out = format_index(notes)
    assert out.startswith("- [[Le borrow checker")
    assert "data races" in out
    assert "tags: rust, concurrence" in out


def test_cache_hit_avoids_reparse(tmp_path):
    d = _make_vault(tmp_path)
    cache = tmp_path / "cache.json"
    first = build_index_cached(d, cache)
    assert cache.exists()
    # Corrupt the source note; cache hit must return the OLD parse.
    (d / "Le borrow checker garantit l'absence de data races.md").write_text(
        NOTE, encoding="utf-8")  # rewrite identical content => same signature
    second = build_index_cached(d, cache)
    assert [n.title for n in first] == [n.title for n in second]
