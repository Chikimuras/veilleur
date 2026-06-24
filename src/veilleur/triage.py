"""Stage 1 — triage: cheaply score every item and keep the best few.

A single batched LLM call scores all parsed items against the user's interests
profile, so the expensive per-item enrichment only ever runs on a short,
relevant shortlist. Items at or above the threshold are kept, sorted by score,
and capped to ``max_items``.
"""

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
    "pertinence) et 1 à 3 tags en kebab-case. Format STRICT: "
    '{"scores": [{"index": <int>, "score": <int>, "tags": ["<tag>"]}]}'
)


def triage(
    items: list[Item],
    interests: str,
    client,
    model: str,
    threshold: int,
    max_items: int,
) -> list[Item]:
    """Score items against the interests profile and return the shortlist.

    Mutates each scored item in place (sets ``score`` and ``tags``).

    Args:
        items: All items parsed from the digest.
        interests: The user's interests profile (markdown text).
        client: Anthropic client, passed through to :func:`llm.call_json`.
        model: Anthropic model id.
        threshold: Minimum score (inclusive) required to be kept.
        max_items: Maximum number of items to return.

    Returns:
        Kept items, sorted by descending score, capped to ``max_items``. Empty
        when ``items`` is empty (no LLM call is made in that case).
    """
    if not items:
        return []
    listing = "\n".join(
        f"{i}. [{'HOT' if it.hot else 'normal'}] {it.title} ({it.source})"
        for i, it in enumerate(items)
    )
    user = f"PROFIL D'INTÉRÊTS:\n{interests}\n\nARTICLES:\n{listing}\n\n{_INSTRUCTIONS}"
    # max_tokens scales with item count: one {index, score, tags} entry per
    # article. 8192 covers a large cold-start digest (no dedup yet) with margin.
    response = llm.call_json(client, model, _SYSTEM, user, max_tokens=8192)
    scored_by_index = {int(s["index"]): s for s in response.get("scores", [])}
    for i, it in enumerate(items):
        scored = scored_by_index.get(i)
        if scored is None:
            continue
        it.score = int(scored["score"])
        it.tags = list(scored.get("tags", []))
    kept = [it for it in items if it.score is not None and it.score >= threshold]
    kept.sort(key=lambda it: it.score, reverse=True)
    return kept[:max_items]
