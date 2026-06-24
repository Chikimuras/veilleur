from dataclasses import dataclass, field


@dataclass
class Connection:
    note_title: str
    reason: str


@dataclass
class Item:
    title: str
    url: str
    source: str
    hot: bool = False
    score: int | None = None
    score_reason: str = ""
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    why: str = ""
    connections: list[Connection] = field(default_factory=list)
    enrich_failed: bool = False
