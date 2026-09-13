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


def ask(prompt, system=None, model=None, max_tokens=8000):
    """Return the model's plain-text reply."""
    kwargs = {
        "model": model or MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    resp = client().messages.create(**kwargs)
    return "".join(b.text for b in resp.content if b.type == "text").strip()


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
