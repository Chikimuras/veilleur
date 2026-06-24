from pathlib import Path

import pytest

from veilleur.config import load_config

TOML = """
model = "claude-sonnet-4-6"
triage_threshold = 6
max_items = 10
vault = "{vault}"
permanent_notes = "30_Permanent_Notes"
inbox = "00_Inbox"
interests = "{interests}"
work_dir = "{work}"
matcha_bin = "matcha"
matcha_version = "v0.9.0"
matcha_config = "{matcha_cfg}"
matcha_file_prefix = ""
matcha_file_suffix = ""
"""


def _write(tmp_path) -> Path:
    vault = tmp_path / "vault"
    (vault / "30_Permanent_Notes").mkdir(parents=True)
    (vault / "00_Inbox").mkdir(parents=True)
    interests = tmp_path / "interests.md"
    interests.write_text("mes intérêts")
    matcha_cfg = tmp_path / "matcha.yaml"
    matcha_cfg.write_text("markdown_dir_path:")
    cfg = tmp_path / "veilleur.toml"
    cfg.write_text(TOML.format(
        vault=vault, interests=interests,
        work=tmp_path / "work", matcha_cfg=matcha_cfg,
    ))
    return cfg


def test_load_resolves_vault_relative_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    cfg = load_config(_write(tmp_path))
    assert cfg.permanent_notes_dir == tmp_path / "vault" / "30_Permanent_Notes"
    assert cfg.inbox_dir == tmp_path / "vault" / "00_Inbox"
    assert cfg.model == "claude-sonnet-4-6"
    assert cfg.triage_threshold == 6
    assert cfg.max_items == 10
    assert cfg.anthropic_api_key == "sk-test"


def test_missing_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(KeyError):
        load_config(_write(tmp_path))
