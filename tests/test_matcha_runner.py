import subprocess
from types import SimpleNamespace

import pytest

from veilleur import matcha_runner


def _cfg(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    return SimpleNamespace(
        matcha_bin="matcha",
        matcha_config=tmp_path / "matcha.yaml",
        work_dir=work,
        matcha_file_prefix="",
        matcha_file_suffix="",
    )


def test_returns_output_path_on_success(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    expected = cfg.work_dir / "2026-06-23.md"

    def fake_run(cmd, **kwargs):
        expected.write_text("### Feed\n[t](u)  \n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(matcha_runner.subprocess, "run", fake_run)
    assert matcha_runner.run_matcha(cfg, today="2026-06-23") == expected


def test_process_failure_raises(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)

    def boom(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="boom")

    monkeypatch.setattr(matcha_runner.subprocess, "run", boom)
    with pytest.raises(matcha_runner.MatchaError):
        matcha_runner.run_matcha(cfg, today="2026-06-23")


def test_missing_output_file_raises(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr(matcha_runner.subprocess, "run",
                        lambda cmd, **k: SimpleNamespace(returncode=0))
    with pytest.raises(matcha_runner.MatchaError):
        matcha_runner.run_matcha(cfg, today="2026-06-23")
