from . import llm
from .models import Item

_SYSTEM = (
    "Tu es l'assistant de veille techno d'un ingénieur qui vise l'expertise. "
    "Tu notes des articles selon leur valeur d'apprentissage pour LUI, en "
    "fonction de son profil d'intérêts. Réponds UNIQUEMENT en JSON."
)

_INSTRUCTIONS = (
    "Pour CHAQUE article, donne un score de 0 à 10 (pertinence vis-à-vis du "
    "profil + valeur d'apprentissage; un article marqué [HOT] est populaire, "
    "pondère légèrement à la hausse mais la popularité ne prime pas sur la "
    "pertinence). Donne une raison courte en français et 1 à 3 tags en "
    'kebab-case. Format STRICT: {"scores": [{"index": <int>, "score": <int>, '
    '"reason": "<fr>", "tags": ["<tag>"]}]}'
)


def triage(items, interests, client, model, threshold, max_items):
    if not items:
        return []
    listing = "\n".join(
        f"{i}. [{'HOT' if it.hot else 'normal'}] {it.title} ({it.source})"
        for i, it in enumerate(items)
    )
    user = f"PROFIL D'INTÉRÊTS:\n{interests}\n\nARTICLES:\n{listing}\n\n{_INSTRUCTIONS}"
    data = llm.call_json(client, model, _SYSTEM, user, max_tokens=2048)
    by_index = {int(d["index"]): d for d in data.get("scores", [])}
    for i, it in enumerate(items):
        d = by_index.get(i)
        if d is None:
            continue
        it.score = int(d["score"])
        it.score_reason = d.get("reason", "")
        it.tags = list(d.get("tags", []))
    kept = [it for it in items if it.score is not None and it.score >= threshold]
    kept.sort(key=lambda it: it.score, reverse=True)
    return kept[:max_items]
