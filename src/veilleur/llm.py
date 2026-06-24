"""Thin Anthropic client wrapper that returns parsed JSON.

Every triage/enrich prompt asks the model for a strict JSON object. This module
centralises sending the prompt, tolerating a ```` ```json ```` code fence around
the reply, parsing it, and retrying transient failures with exponential backoff.
``sleep`` is injectable so tests run without real delays.
"""

import json
import time

import anthropic


class LLMError(Exception):
    """Raised when an LLM call still fails after all retries."""


def make_client(api_key: str) -> anthropic.Anthropic:
    """Create an Anthropic client for the given API key."""
    return anthropic.Anthropic(api_key=api_key)


def _extract_json(text: str) -> str:
    """Return the JSON payload from a reply, unwrapping a ```` ``` ```` fence."""
    text = text.strip()
    if text.startswith("```"):
        inner = text.split("```")[1]
        if inner.startswith("json"):
            inner = inner[len("json"):]
        return inner.strip()
    return text


def call_json(client, model, system, user, *, max_tokens=2048, retries=3, sleep=time.sleep):
    """Send a single-message prompt and return the parsed JSON response.

    Args:
        client: An Anthropic client (see :func:`make_client`).
        model: Anthropic model id.
        system: System prompt.
        user: User message content.
        max_tokens: Max tokens for the response (size it to the expected output).
        retries: Number of attempts before giving up.
        sleep: Sleep function used for backoff between attempts (injectable for
            tests).

    Returns:
        The parsed JSON object (a ``dict``).

    Raises:
        LLMError: If every attempt fails (network, API, or JSON-parse error).
    """
    last_error = None
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
            last_error = exc
            if attempt < retries - 1:
                sleep(2 ** attempt)
    raise LLMError(f"LLM call failed after {retries} attempts: {last_error}")
