import subprocess
from datetime import date
from pathlib import Path


class MatchaError(Exception):
    pass


def run_matcha(cfg, today: str | None = None) -> Path:
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
    out = cfg.work_dir / f"{cfg.matcha_file_prefix}{today}{cfg.matcha_file_suffix}.md"
    if not out.exists():
        raise MatchaError(f"matcha produced no output at {out}")
    return out
