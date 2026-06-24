"""Invoke the external matcha binary and locate its output.

matcha (https://github.com/piqoni/matcha) is treated as an unmodified, pinned
black box: this module shells out to it and returns the path to today's digest
file. It is fail-safe — any process failure, or a missing output file, raises
:class:`MatchaError` so the orchestrator writes no note rather than a broken one.
"""

import subprocess
from datetime import date
from pathlib import Path


class MatchaError(Exception):
    """Raised when matcha fails to run or produces no output file."""


def run_matcha(cfg, today: str | None = None) -> Path:
    """Run matcha and return the path to its digest for ``today``.

    Args:
        cfg: A :class:`~veilleur.config.Config`-like object providing
            ``matcha_bin``, ``matcha_config``, ``work_dir`` and the filename
            prefix/suffix.
        today: ISO date (``YYYY-MM-DD``) for the expected output filename;
            defaults to the current date.

    Returns:
        Path to matcha's markdown digest for ``today``.

    Raises:
        MatchaError: If the matcha process fails (non-zero exit, missing binary,
            timeout) or if the expected output file is not produced.
    """
    today = today or date.today().isoformat()
    cmd = [cfg.matcha_bin, "-c", str(cfg.matcha_config)]
    try:
        subprocess.run(
            cmd,
            cwd=str(cfg.work_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired) as exc:
        raise MatchaError(f"matcha run failed: {exc}") from exc
    # matcha names its output file `{MarkdownFilePrefix}{date}{MarkdownFileSuffix}.md`
    # with date = time.Now().Format("2006-01-02") (ISO) — see matcha config.go /
    # markdown_writer.go NewMarkdownWriter. If matcha changes this scheme, update here.
    out = cfg.work_dir / f"{cfg.matcha_file_prefix}{today}{cfg.matcha_file_suffix}.md"
    if not out.exists():
        raise MatchaError(f"matcha produced no output at {out}")
    return out
