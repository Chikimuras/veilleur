import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_CONCEPT = re.compile(r"##\s*💡[^\n]*\n(.*?)(?=\n##|\Z)", re.DOTALL)
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


@dataclass
class VaultNote:
    title: str
    concept: str
    tags: list[str]


def _parse_concept(text: str) -> str:
    m = _CONCEPT.search(text)
    if not m:
        return ""
    body = m.group(1).strip()
    # Strip leading blockquote markers and whitespace from each line.
    lines = [re.sub(r"^>\s*", "", ln).strip() for ln in body.splitlines()]
    return " ".join(ln for ln in lines if ln)


def _parse_tags(text: str) -> list[str]:
    fm = _FRONTMATTER.search(text)
    if not fm:
        return []
    tags: list[str] = []
    in_tags = False
    for line in fm.group(1).splitlines():
        if re.match(r"^tags:\s*$", line):
            in_tags = True
            continue
        if in_tags:
            m = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if m:
                tags.append(m.group(1))
            elif line.strip() and not line.startswith(" "):
                break
    return tags


def parse_note(path: Path) -> VaultNote:
    text = path.read_text(encoding="utf-8")
    return VaultNote(
        title=path.stem,
        concept=_parse_concept(text),
        tags=_parse_tags(text),
    )


def build_index(permanent_dir: Path) -> list[VaultNote]:
    return [parse_note(p) for p in sorted(permanent_dir.glob("*.md"))]


def _signature(permanent_dir: Path) -> str:
    parts = sorted(
        (p.name, p.stat().st_mtime_ns) for p in permanent_dir.glob("*.md")
    )
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def build_index_cached(permanent_dir: Path, cache_path: Path) -> list[VaultNote]:
    sig = _signature(permanent_dir)
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("sig") == sig:
            return [VaultNote(**n) for n in cached["notes"]]
    notes = build_index(permanent_dir)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"sig": sig, "notes": [asdict(n) for n in notes]}),
        encoding="utf-8",
    )
    return notes


def format_index(notes: list[VaultNote]) -> str:
    lines = []
    for n in notes:
        tagstr = f" [tags: {', '.join(n.tags)}]" if n.tags else ""
        lines.append(f"- [[{n.title}]]: {n.concept}{tagstr}")
    return "\n".join(lines)
