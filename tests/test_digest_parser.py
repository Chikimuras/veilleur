from pathlib import Path

from veilleur.digest_parser import parse_digest

FIXTURE = Path(__file__).parent / "fixtures" / "matcha_output.md"


def test_parses_all_articles():
    items = parse_digest(FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 4


def test_hn_hot_flag_and_article_url():
    items = parse_digest(FIXTURE.read_text(encoding="utf-8"))
    hot = items[0]
    assert hot.title == "Rust async runtime internals"
    assert hot.url == "https://example.com/rust-async"
    assert hot.hot is True
    assert hot.source == "Hacker News: Best"
    assert items[1].hot is False  # 💬 = not hot


def test_non_hn_items_have_clean_source_and_no_icon():
    items = parse_digest(FIXTURE.read_text(encoding="utf-8"))
    tonsky = items[2]
    assert tonsky.title == "Software disenchantment"
    assert tonsky.url == "https://tonsky.me/blog/disenchantment"
    assert tonsky.source == "Tonsky"
    assert tonsky.hot is False
    assert items[3].source == "Some Blog"  # 🍵 stripped


def test_empty_input_returns_empty_list():
    assert parse_digest("") == []
