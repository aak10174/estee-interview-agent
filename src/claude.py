"""Thin wrapper around the Anthropic Messages API.

Single place where the model is called, so swapping keys or models is a
one-line change for whoever inherits this repo.
"""
import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, MODEL, require

_client = None


def client():
    global _client
    if _client is None:
        require("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def ask(prompt, system=None, model=None, max_tokens=8000, cache_system=False):
    """Return the model's plain-text reply.

    cache_system=True marks the system prompt as cacheable for an hour. Use it
    when the same large block (the whole vault) is sent again and again — a
    cache hit costs a tenth of a fresh read. Caching is a prefix match, so the
    varying part (the question) must stay in the message, never in the system.
    """
    kwargs = {
        "model": model or MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system and cache_system:
        kwargs["system"] = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ]
    elif system:
        kwargs["system"] = system

    resp = client().messages.create(**kwargs)
    _log_usage(resp)
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _log_usage(resp):
    """Print what the call cost in tokens. Cheap insurance against surprises."""
    u = resp.usage
    cached = getattr(u, "cache_read_input_tokens", 0) or 0
    note = "  (%d from cache)" % cached if cached else ""
    print(
        "    %s: %d in / %d out%s"
        % (resp.model, u.input_tokens, u.output_tokens, note)
    )


def ask_json(prompt, system=None, model=None, max_tokens=8000):
    """Ask for JSON and parse it, tolerating stray prose or code fences."""
    raw = ask(
        prompt + "\n\nReply with valid JSON only. No prose, no code fences.",
        system=system,
        model=model,
        max_tokens=max_tokens,
    )
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.S)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: grab the outermost JSON object in the reply.
        span = re.search(r"\{.*\}", raw, re.S)
        if not span:
            raise
        return json.loads(span.group(0))
