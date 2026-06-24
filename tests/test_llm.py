import pytest

from veilleur import llm


class _Block:
    def __init__(self, text):
        self.text = text


class _Msg:
    def __init__(self, text):
        self.content = [_Block(text)]


class _Client:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = 0

        class _Messages:
            def create(inner, **kwargs):
                self.calls += 1
                r = self._responses.pop(0)
                if isinstance(r, Exception):
                    raise r
                return _Msg(r)

        self.messages = _Messages()


def test_parses_plain_json():
    client = _Client('{"a": 1}')
    assert llm.call_json(client, "m", "sys", "usr") == {"a": 1}


def test_strips_json_code_fence():
    client = _Client('```json\n{"a": 2}\n```')
    assert llm.call_json(client, "m", "sys", "usr") == {"a": 2}


def test_retries_then_succeeds():
    client = _Client(RuntimeError("flaky"), '{"ok": true}')
    out = llm.call_json(client, "m", "s", "u", sleep=lambda _: None)
    assert out == {"ok": True}
    assert client.calls == 2


def test_raises_after_exhausting_retries():
    client = _Client(RuntimeError("a"), RuntimeError("b"), RuntimeError("c"))
    with pytest.raises(llm.LLMError):
        llm.call_json(client, "m", "s", "u", retries=3, sleep=lambda _: None)
