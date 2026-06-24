"""Build a compact index of existing permanent notes.

The enrichment stage needs a cheap, high-signal view of the Zettelkasten so the
LLM can suggest connections without reading every note in full. This module
extracts ``{title, concept, tags}`` from each permanent note — the title is the
filename, the concept is the one-sentence ``## 💡`` blockquote, and the tags
come from the YAML frontmatter — and formats them as a wikilink listing.

Results are cached to JSON keyed on a signature of the notes' filenames and
modification times, so the index is only rebuilt when the vault changes.
"""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

# The "concept en une phrase" block: text under a ``## 💡 …`` heading, up to the
# next ``##`` heading or end of file.
_CONCEPT = re.compile(r"##\s*💡[^\n]*\n(.*?)(?=\n##|\Z)", re.DOTALL)
# The YAML frontmatter block delimited by leading ``---`` fences.
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


@dataclass
class VaultNote:
    """A permanent note reduced to what the connection step needs.

    Attributes:
        title: Note title (the markdown filename without extension).
        concept: The one-sentence concept from the ``## 💡`` section, if any.
        tags: Frontmatter tags.
    """

    title: str
    concept: str
    tags: list[str]


def _parse_concept(text: str) -> str:
    """Return the ``## 💡`` concept sentence, blockquote markers stripped."""
    match = _CONCEPT.search(text)
    if not match:
        return ""
    body = match.group(1).strip()
    lines = [re.sub(r"^>\s*", "", line).strip() for line in body.splitlines()]
    return " ".join(line for line in lines if line)


def _parse_tags(text: str) -> list[str]:
    """Return the list items under the frontmatter ``tags:`` key."""
    frontmatter = _FRONTMATTER.search(text)
    if not frontmatter:
        return []
    tags: list[str] = []
    in_tags = False
    for line in frontmatter.group(1).splitlines():
        if re.match(r"^tags:\s*$", line):
            in_tags = True
            continue
        if in_tags:
            item = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if item:
                tags.append(item.group(1))
            elif line.strip() and not line.startswith(" "):
                break  # reached the next top-level frontmatter key
    return tags


def parse_note(path: Path) -> VaultNote:
    """Parse a single permanent-note markdown file into a :class:`VaultNote`."""
    text = path.read_text(encoding="utf-8")
    return VaultNote(
        title=path.stem,
        concept=_parse_concept(text),
        tags=_parse_tags(text),
    )


def build_index(permanent_dir: Path) -> list[VaultNote]:
    """Parse every ``*.md`` in ``permanent_dir`` (sorted by filename)."""
    return [parse_note(p) for p in sorted(permanent_dir.glob("*.md"))]


def _signature(permanent_dir: Path) -> str:
    """A hash of (filename, mtime) pairs; changes whenever the vault changes."""
    parts = sorted(
        (p.name, p.stat().st_mtime_ns) for p in permanent_dir.glob("*.md")
    )
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def build_index_cached(permanent_dir: Path, cache_path: Path) -> list[VaultNote]:
    """Like :func:`build_index`, but served from ``cache_path`` when fresh.

    The cache is reused as long as the vault signature is unchanged; otherwise
    the notes are reparsed and the cache is rewritten.
    """
    sig = _signature(permanent_dir)
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("sig") == sig:
            return [VaultNote(**note) for note in cached["notes"]]
    notes = build_index(permanent_dir)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"sig": sig, "notes": [asdict(note) for note in notes]}),
        encoding="utf-8",
    )
    return notes


def format_index(notes: list[VaultNote]) -> str:
    """Render the index as a compact wikilink listing for the LLM prompt.

    Each line is ``- [[Title]]: concept [tags: a, b]`` (tags omitted if empty).
    """
    lines = []
    for note in notes:
        tag_suffix = f" [tags: {', '.join(note.tags)}]" if note.tags else ""
        lines.append(f"- [[{note.title}]]: {note.concept}{tag_suffix}")
    return "\n".join(lines)
