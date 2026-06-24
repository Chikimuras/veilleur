"""Configuration loading.

Reads a small TOML file describing where the Obsidian vault lives, how to
invoke matcha, and a few tuning knobs. The Anthropic API key is read from the
``ANTHROPIC_API_KEY`` environment variable and is never stored in the config
file.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Resolved configuration for a veilleur run.

    Paths are already expanded (``~`` resolved) and, for the vault-relative
    directories, joined onto the vault root.

    Attributes:
        vault_path: Root of the Obsidian vault.
        permanent_notes_dir: Folder of permanent notes scanned for connections.
        inbox_dir: Folder the daily veille note is written to.
        interests_path: Path to the interests/profile markdown file.
        work_dir: Scratch directory for matcha output and the vault-index cache.
        matcha_bin: matcha executable (name on PATH, or an absolute path).
        matcha_config: Path to matcha's own ``config.yaml``.
        matcha_version: Pinned matcha version, for documentation/provenance.
        matcha_file_prefix: Prefix matcha uses in its output filename.
        matcha_file_suffix: Suffix matcha uses in its output filename.
        model: Anthropic model id used for triage and enrichment.
        triage_threshold: Minimum score (0-10) an item must reach to be kept.
        max_items: Maximum number of items to keep in a digest.
        anthropic_api_key: API key, read from the environment.
    """

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
    """Turn a config string into a Path with ``~`` expanded to the home dir."""
    return Path(value).expanduser()


def load_config(path: Path) -> Config:
    """Load and resolve the TOML config at ``path``.

    Args:
        path: Path to the ``veilleur.toml`` file.

    Returns:
        A fully-resolved :class:`Config`.

    Raises:
        KeyError: If a required key is missing, or if the ``ANTHROPIC_API_KEY``
            environment variable is not set.
    """
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
