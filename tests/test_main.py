from pathlib import Path
from types import SimpleNamespace

from veilleur import main as main_mod

DIGEST = """
### <img src="x" /> Hacker News: Best
[🔥 ](https://news.ycombinator.com/item?id=1)[Rust async internals](https://ex.com/a)

### 🍵 Blog
[Some hype post](https://ex.com/b)
"""


def _wire(tmp_path, monkeypatch):
    inbox = tmp_path / "00_Inbox"
    inbox.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    perm = tmp_path / "30_Permanent_Notes"
    perm.mkdir()
    interests = tmp_path / "interests.md"
    interests.write_text("rust, systèmes distribués", encoding="utf-8")

    cfg = SimpleNamespace(
        permanent_notes_dir=perm, inbox_dir=inbox, work_dir=work,
        interests_path=interests, model="m", triage_threshold=6, max_items=10,
        anthropic_api_key="sk", matcha_bin="matcha",
        matcha_config=tmp_path / "m.yaml", matcha_version="v0.9.0",
        matcha_file_prefix="", matcha_file_suffix="",
    )
    monkeypatch.setattr(main_mod.config, "load_config", lambda p: cfg)

    digest = work / "2026-06-23.md"
    monkeypatch.setattr(main_mod.matcha_runner, "run_matcha",
                        lambda c, today=None: (digest.write_text(DIGEST), digest)[1])
    monkeypatch.setattr(main_mod.llm, "make_client", lambda key: object())

    def fake_call(client, model, system, user, **k):
        if "ARTICLES:" in user:  # triage
            return {"scores": [
                {"index": 0, "score": 9, "reason": "cible", "tags": ["rust"]},
                {"index": 1, "score": 2, "reason": "hype", "tags": ["hype"]},
            ]}
        return {"summary": "résumé", "why": "pour progresser", "connections": []}

    monkeypatch.setattr(main_mod.llm, "call_json", fake_call)
    monkeypatch.setattr(main_mod.content_fetch, "fetch_text", lambda url: "body")
    return cfg, inbox


def test_writes_note_with_only_kept_items(tmp_path, monkeypatch):
    cfg, inbox = _wire(tmp_path, monkeypatch)
    rc = main_mod.main(["--date", "2026-06-23"])
    assert rc == 0
    note = inbox / "2026-06-23-veille.md"
    assert note.exists()
    text = note.read_text(encoding="utf-8")
    assert "type: veille" in text
    assert "Rust async internals" in text       # kept (score 9)
    assert "Some hype post" not in text          # dropped (score 2)
    assert "1 articles retenus sur 2 analysés." in text


def test_idempotent_skip_without_force(tmp_path, monkeypatch):
    cfg, inbox = _wire(tmp_path, monkeypatch)
    (inbox / "2026-06-23-veille.md").write_text("déjà là", encoding="utf-8")
    rc = main_mod.main(["--date", "2026-06-23"])
    assert rc == 0
    assert (inbox / "2026-06-23-veille.md").read_text(encoding="utf-8") == "déjà là"
