"""Core data structures shared across the veilleur pipeline.

A single :class:`Item` instance flows through every stage and is mutated in
place: the digest parser creates it (title/url/source/hot), triage fills the
score and tags, and enrich fills the summary, the "why", and the connections.
The renderer reads the fully-populated item at the end.
"""

from dataclasses import dataclass, field


@dataclass
class Connection:
    """A suggested link from an article to an existing Zettelkasten note.

    Attributes:
        note_title: Exact title of an existing permanent note (no ``[[ ]]``).
        reason: Short French explanation of why the article resonates with it.
    """

    note_title: str
    reason: str


@dataclass
class Item:
    """One article as it travels through the pipeline.

    Created by the digest parser with the first four fields; the remaining
    fields are filled by later stages (triage, then enrich) and stay at their
    defaults if a stage is skipped or fails.

    Attributes:
        title: Article title.
        url: Canonical article URL (not the discussion/comments URL).
        source: Human-readable feed name the item came from.
        hot: True when the source flagged the item as popular (matcha's 🔥 on
            Hacker News items with >=100 comments). No signal => False.
        score: Triage relevance score from 0 to 10, or None if not scored.
        score_reason: Reserved for an optional triage rationale (unused by the
            renderer; kept for debugging/extension).
        tags: Kebab-case topic tags assigned during triage.
        summary: French summary produced during enrichment.
        why: One-line "why it matters to you" produced during enrichment.
        connections: Suggested links to existing permanent notes.
        enrich_failed: True if enrichment failed for this item (it is still
            rendered, with a visible notice, rather than dropped).
    """

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
