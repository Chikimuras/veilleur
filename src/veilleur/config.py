import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    vault_path: Path
    permanent_notes_dir: Path
    inbox_dir: Path
    interests_path: Path
    work_dir: Path
    matcha_bin: str
    matcha_config: Path
    matcha_version: str
    matcha_file_prefix: str
    matcha_file_suffix: str
    model: str
    triage_threshold: int
    max_items: int
    anthropic_api_key: str


def _expand(value: str) -> Path:
    return Path(value).expanduser()


def load_config(path: Path) -> Config:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    vault = _expand(data["vault"])
    return Config(
        vault_path=vault,
        permanent_notes_dir=vault / data["permanent_notes"],
        inbox_dir=vault / data["inbox"],
        interests_path=_expand(data["interests"]),
        work_dir=_expand(data["work_dir"]),
        matcha_bin=data["matcha_bin"],
        matcha_config=_expand(data["matcha_config"]),
        matcha_version=data["matcha_version"],
        matcha_file_prefix=data.get("matcha_file_prefix", ""),
        matcha_file_suffix=data.get("matcha_file_suffix", ""),
        model=data["model"],
        triage_threshold=int(data["triage_threshold"]),
        max_items=int(data["max_items"]),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
    )
