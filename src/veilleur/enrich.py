from . import llm
from .models import Connection, Item


def _clean_note_title(raw: str) -> str:
    """Strip any surrounding [[ ]] the LLM may echo from the vault index, so the
    renderer wraps the title exactly once (avoids broken [[[[...]]]] wikilinks)."""
    title = raw.strip()
    if title.startswith("[[") and title.endswith("]]"):
        title = title[2:-2].strip()
    return title

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


def enrich_item(item, vault_index_str, client, model, fetch):
    content = fetch(item.url)
    body = content if content else "(contenu indisponible — base-toi sur le titre)"
    user = (
        f"ARTICLE: {item.title}\nSOURCE: {item.source}\nURL: {item.url}\n\n"
        f"CONTENU:\n{body}\n\n"
        f"NOTES EXISTANTES DU VAULT:\n{vault_index_str}\n\n{_INSTRUCTIONS}"
    )
    try:
        data = llm.call_json(client, model, _SYSTEM, user, max_tokens=1500)
    except llm.LLMError:
        item.enrich_failed = True
        return item
    item.summary = data.get("summary", "")
    item.why = data.get("why", "")
    item.connections = [
        Connection(note_title=_clean_note_title(c["note"]), reason=c.get("reason", ""))
        for c in data.get("connections", [])
    ]
    return item
