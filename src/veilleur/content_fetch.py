import httpx
import trafilatura

_HEADERS = {"User-Agent": "veilleur/0.1 (+https://github.com/alexandre)"}


def fetch_text(url: str, *, timeout: float = 20.0, max_chars: int = 8000) -> str | None:
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True, headers=_HEADERS)
        resp.raise_for_status()
    except Exception:
        return None
    extracted = trafilatura.extract(resp.text)
    if not extracted:
        return None
    return extracted[:max_chars]
