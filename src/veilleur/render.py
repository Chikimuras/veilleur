"""Render the enriched shortlist into the daily Zettelkasten note.

Produces a markdown note matching the Obsidian vault conventions: frontmatter
with ``type: veille`` / ``status: ⏳``, an emoji H1, and one section per item
with its source/score, tags, summary, rationale and connection wikilinks. The
``### 🔗 Connexions`` heading mirrors the permanent-note template so an item can
be promoted to a permanent note by copy-paste.
"""

from .models import Item


def render_note(items: list[Item], date_str: str, n_analyzed: int) -> str:
    """Render the daily veille note.

    Args:
        items: The kept, enriched items (already sorted by the pipeline).
        date_str: ISO date used in the frontmatter and title.
        n_analyzed: Total number of items considered before triage (for the
            "N retenus sur M analysés" summary line).

    Returns:
        The full markdown document, ending with a single trailing newline.
    """
    lines = [
        "---",
        "type: veille",
        "status: ⏳",
        f"date: {date_str}",
        "tags:",
        "  - veille",
        "---",
        "",
        f"# 📡 Veille — {date_str}",
        "",
        f"> {len(items)} articles retenus sur {n_analyzed} analysés.",
        "",
    ]
    for item in items:
        lines.append(f"## [{item.title}]({item.url})")
        hot = " · 🔥" if item.hot else ""
        score = f" · **Score :** {item.score}/10" if item.score is not None else ""
        lines.append(f"**Source :** {item.source}{hot}{score}")
        if item.tags:
            lines.append(f"**Tags :** {', '.join(item.tags)}")
        lines.append("")
        if item.enrich_failed:
            lines.append("_Résumé indisponible (enrichissement échoué)._")
            lines.append("")
        else:
            if item.summary:
                lines.append(item.summary)
                lines.append("")
            if item.why:
                lines.append(f"**Pourquoi pour toi :** {item.why}")
                lines.append("")
        lines.append("### 🔗 Connexions")
        if item.connections:
            for connection in item.connections:
                lines.append(f"- [[{connection.note_title}]] — {connection.reason}")
        else:
            lines.append("- [[ ]]")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
