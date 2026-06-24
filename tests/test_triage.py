from veilleur import triage as triage_mod
from veilleur.models import Item


def _items():
    return [
        Item(title="Rust internals", url="u1", source="HN", hot=True),
        Item(title="Crypto moon hype", url="u2", source="HN"),
        Item(title="Distributed consensus", url="u3", source="Blog"),
    ]


def _fake_scores(monkeypatch):
    payload = {"scores": [
        {"index": 0, "score": 9, "reason": "pile dans ta cible", "tags": ["rust"]},
        {"index": 1, "score": 2, "reason": "hype", "tags": ["crypto"]},
        {"index": 2, "score": 7, "reason": "fondamental", "tags": ["distsys"]},
    ]}
    monkeypatch.setattr(triage_mod.llm, "call_json", lambda *a, **k: payload)


def test_filters_below_threshold_and_sorts(monkeypatch):
    _fake_scores(monkeypatch)
    kept = triage_mod.triage(_items(), "profil", client=None,
                             model="m", threshold=6, max_items=10)
    assert [it.title for it in kept] == ["Rust internals", "Distributed consensus"]
    assert kept[0].score == 9
    assert kept[0].tags == ["rust"]


def test_respects_max_items(monkeypatch):
    _fake_scores(monkeypatch)
    kept = triage_mod.triage(_items(), "profil", client=None,
                             model="m", threshold=1, max_items=1)
    assert len(kept) == 1
    assert kept[0].title == "Rust internals"


def test_empty_items_returns_empty(monkeypatch):
    # call_json must NOT be invoked when there is nothing to score.
    monkeypatch.setattr(triage_mod.llm, "call_json",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert triage_mod.triage([], "profil", None, "m", 6, 10) == []
