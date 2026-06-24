"""Best-effort article text extraction.

The enrichment stage wants the body of an article to summarise. Fetching is
deliberately best-effort: any failure (network error, non-2xx, or nothing
extractable) returns ``None`` so the pipeline can fall back to the title and
keep going rather than aborting the whole digest over one bad URL.
"""

import httpx
import trafilatura

_HEADERS = {"User-Agent": "veilleur/0.1 (+https://github.com/Chikimuras/veilleur)"}


def fetch_text(url: str, *, timeout: float = 20.0, max_chars: int = 8000) -> str | None:
    """Fetch ``url`` and return its main text content, or ``None`` on failure.

    Args:
        url: The article URL to fetch.
        timeout: Per-request timeout in seconds.
        max_chars: Hard cap on the returned text length (keeps LLM input bounded).

    Returns:
        The extracted article text truncated to ``max_chars``, or ``None`` if the
        request failed or no readable content could be extracted.
    """
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True, headers=_HEADERS)
        resp.raise_for_status()
    except Exception:
        return None
    extracted = trafilatura.extract(resp.text)
    if not extracted:
        return None
    return extracted[:max_chars]
