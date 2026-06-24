"""Stage 2 — enrich: summarise an item and link it into the Zettelkasten.

For each item that survived triage, fetch the article text and ask the LLM for
a French summary, a one-line "why it matters", and connections to existing
permanent notes. Enrichment is fault-isolated per item: if the LLM call fails,
the item is flagged (``enrich_failed``) and returned rather than dropped, so one
failure never sinks the whole digest.
"""

from collections.abc import Callable

from . import llm
from .models import Connection, Item

_SYSTEM = (
    "Tu es l'assistant de veille d'un ingénieur. Pour un article donné, tu "
    "produis un résumé en français, expliques pourquoi il vaut son temps au "
    "regard de sa montée en expertise, et proposes des connexions UNIQUEMENT "
    "vers des notes existantes de son Zettelkasten (jamais inventées). "
    "Réponds UNIQUEMENT en JSON."
)

_INSTRUCTIONS = (
    "Format STRICT: {\"summary\": \"<2-3 phrases fr>\", \"why\": \"<1 phrase "
    "fr>\", \"connections\": [{\"note\": \"<titre EXACT d'une note de la liste "
    "ci-dessus>\", \"reason\": \"<fr, pourquoi ça résonne>\"}]}. Si aucune note "
    "ne résonne vraiment, renvoie une liste connections vide."
)


def _clean_note_title(raw: str) -> str:
    """Strip any surrounding ``[[ ]]`` the LLM may echo from the vault index.

    The index is presented to the model as ``[[Title]]`` lines, so it sometimes
    returns the wrapped form. Stripping it here lets the renderer wrap the title
    exactly once (avoids broken ``[[[[...]]]]`` wikilinks).
    """
    title = raw.strip()
    if title.startswith("[[") and title.endswith("]]"):
        title = title[2:-2].strip()
    return title


def enrich_item(
    item: Item,
    vault_index_str: str,
    client,
    model: str,
    fetch: Callable[[str], str | None],
) -> Item:
    """Enrich a single item with a summary, a rationale and connections.

    Args:
        item: The item to enrich (mutated in place and returned).
        vault_index_str: The formatted vault index (see ``vault_index``).
        client: Anthropic client, passed through to :func:`llm.call_json`.
        model: Anthropic model id.
        fetch: Callable returning article text for a URL, or ``None`` on failure
            (typically ``content_fetch.fetch_text``).

    Returns:
        The same ``item``, with ``summary``, ``why`` and ``connections`` filled
        on success, or ``enrich_failed=True`` set if the LLM call failed.
    """
    content = fetch(item.url)
    body = content if content else "(contenu indisponible — base-toi sur le titre)"
    user = (
        f"ARTICLE: {item.title}\nSOURCE: {item.source}\nURL: {item.url}\n\n"
        f"CONTENU:\n{body}\n\n"
        f"NOTES EXISTANTES DU VAULT:\n{vault_index_str}\n\n{_INSTRUCTIONS}"
    )
    try:
        response = llm.call_json(client, model, _SYSTEM, user, max_tokens=1500)
    except llm.LLMError:
        item.enrich_failed = True
        return item
    item.summary = response.get("summary", "")
    item.why = response.get("why", "")
    item.connections = [
        Connection(note_title=_clean_note_title(conn["note"]), reason=conn.get("reason", ""))
        for conn in response.get("connections", [])
    ]
    return item
