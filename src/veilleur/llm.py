import json
import time

import anthropic


class LLMError(Exception):
    pass


def make_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        inner = text.split("```")[1]
        if inner.startswith("json"):
            inner = inner[len("json"):]
        return inner.strip()
    return text


def call_json(client, model, system, user, *, max_tokens=2048, retries=3, sleep=time.sleep):
    last = None
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return json.loads(_extract_json(msg.content[0].text))
        except Exception as exc:  # network, parse, API errors all retry
            last = exc
            if attempt < retries - 1:
                sleep(2 ** attempt)
    raise LLMError(f"LLM call failed after {retries} attempts: {last}")
