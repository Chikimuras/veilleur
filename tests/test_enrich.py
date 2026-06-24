from veilleur import enrich as enrich_mod
from veilleur.models import Item


def test_connection_titles_are_unwrapped(monkeypatch):
    # The LLM sometimes echoes the [[ ]] from the vault index; enrich must strip
    # it so the renderer doesn't produce broken [[[[...]]]] wikilinks.
    payload = {
        "summary": "s", "why": "w",
        "connections": [
            {"note": "[[Une note entourée]]", "reason": "r1"},
            {"note": "Une note nue", "reason": "r2"},
        ],
    }
    monkeypatch.setattr(enrich_mod.llm, "call_json", lambda *a, **k: payload)
    it = Item(title="T", url="u", source="HN")
    out = enrich_mod.enrich_item(it, "index", None, "m", fetch=lambda url: "body")
    assert out.connections[0].note_title == "Une note entourée"
    assert out.connections[1].note_title == "Une note nue"


def test_enriches_summary_why_and_connections(monkeypatch):
    payload = {
        "summary": "Un résumé clair.",
        "why": "Approfondit les runtimes async.",
        "connections": [
            {"note": "Le borrow checker garantit l'absence de data races",
             "reason": "même socle ownership"},
        ],
    }
    monkeypatch.setattr(enrich_mod.llm, "call_json", lambda *a, **k: payload)
    it = Item(title="Rust internals", url="u", source="HN")
    out = enrich_mod.enrich_item(it, "index", client=None, model="m",
                                 fetch=lambda url: "article body")
    assert out.summary == "Un résumé clair."
    assert out.why.startswith("Approfondit")
    assert out.connections[0].note_title.startswith("Le borrow checker")
    assert out.connections[0].reason == "même socle ownership"
    assert out.enrich_failed is False


def test_fetch_failure_still_calls_llm_with_placeholder(monkeypatch):
    seen = {}

    def fake_call(client, model, system, user, **k):
        seen["user"] = user
        return {"summary": "s", "why": "w", "connections": []}

    monkeypatch.setattr(enrich_mod.llm, "call_json", fake_call)
    it = Item(title="T", url="u", source="HN")
    enrich_mod.enrich_item(it, "index", None, "m", fetch=lambda url: None)
    assert "indisponible" in seen["user"]


def test_llm_error_sets_failed_flag(monkeypatch):
    def boom(*a, **k):
        raise enrich_mod.llm.LLMError("down")

    monkeypatch.setattr(enrich_mod.llm, "call_json", boom)
    it = Item(title="T", url="u", source="HN")
    out = enrich_mod.enrich_item(it, "index", None, "m", fetch=lambda url: "body")
    assert out.enrich_failed is True
