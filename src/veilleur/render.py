from .models import Item


def render_note(items: list[Item], date_str: str, n_analyzed: int) -> str:
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
    for it in items:
        lines.append(f"## [{it.title}]({it.url})")
        hot = " · 🔥" if it.hot else ""
        score = f" · **Score :** {it.score}/10" if it.score is not None else ""
        lines.append(f"**Source :** {it.source}{hot}{score}")
        if it.tags:
            lines.append(f"**Tags :** {', '.join(it.tags)}")
        lines.append("")
        if it.enrich_failed:
            lines.append("_Résumé indisponible (enrichissement échoué)._")
            lines.append("")
        else:
            if it.summary:
                lines.append(it.summary)
                lines.append("")
            if it.why:
                lines.append(f"**Pourquoi pour toi :** {it.why}")
                lines.append("")
        lines.append("### 🔗 Connexions")
        if it.connections:
            for c in it.connections:
                lines.append(f"- [[{c.note_title}]] — {c.reason}")
        else:
            lines.append("- [[ ]]")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
