import httpx

from veilleur import content_fetch


class _Resp:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_returns_extracted_text(monkeypatch):
    monkeypatch.setattr(
        content_fetch.httpx, "get", lambda *a, **k: _Resp("<html>raw</html>"))
    monkeypatch.setattr(
        content_fetch.trafilatura, "extract", lambda html: "Clean article body")
    assert content_fetch.fetch_text("https://x") == "Clean article body"


def test_truncates_to_max_chars(monkeypatch):
    monkeypatch.setattr(content_fetch.httpx, "get", lambda *a, **k: _Resp("h"))
    monkeypatch.setattr(content_fetch.trafilatura, "extract", lambda html: "a" * 100)
    assert len(content_fetch.fetch_text("https://x", max_chars=10)) == 10


def test_http_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("nope")

    monkeypatch.setattr(content_fetch.httpx, "get", boom)
    assert content_fetch.fetch_text("https://x") is None


def test_no_extractable_content_returns_none(monkeypatch):
    monkeypatch.setattr(content_fetch.httpx, "get", lambda *a, **k: _Resp("h"))
    monkeypatch.setattr(content_fetch.trafilatura, "extract", lambda html: None)
    assert content_fetch.fetch_text("https://x") is None
