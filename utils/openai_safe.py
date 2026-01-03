"""
Utilities for robust handling of OpenAI API responses across both
Chat Completions (/v1/chat/completions) and Responses API (/v1/responses).

Goals:
- Avoid "Response contained no choices" by parsing the right shape
- Provide a single extract_text() that works for both endpoints
- Optional simple retry/backoff helpers

Usage (chat):
    from openai import OpenAI
    from utils.openai_safe import extract_text

    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":"ping"}],
        max_tokens=128,
        n=1,
        temperature=0.2,
    )
    text = extract_text(resp)

Usage (responses):
    resp = client.responses.create(model="gpt-4o-mini", input="ping")
    text = extract_text(resp)
"""
from __future__ import annotations
import time
from typing import Any, Optional


def _from_chat_completions(resp: Any) -> Optional[str]:
    try:
        choices = getattr(resp, "choices", None) or resp.get("choices")  # type: ignore
        if not choices:
            return None
        msg = choices[0].get("message") if isinstance(choices[0], dict) else getattr(choices[0], "message", None)
        if not msg:
            return None
        # If the model returned tool_calls only, content may be None
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if content:
            return str(content)
        # If only tool_calls exist, extract a readable placeholder
        tool_calls = msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)
        if tool_calls:
            return "[tool_calls emitted; no textual content]"
        return None
    except Exception:
        return None


def _from_responses_api(resp: Any) -> Optional[str]:
    # New Responses API shape: prefer output_text when available
    try:
        text = getattr(resp, "output_text", None)
        if text:
            return str(text)
    except Exception:
        pass
    # Fallback: walk through output[].content[].text
    try:
        output = getattr(resp, "output", None) or resp.get("output")  # type: ignore
        if not output:
            return None
        parts = []
        for item in output:
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if not content:
                continue
            for ch in content:
                if isinstance(ch, dict) and ch.get("type") == "output_text":
                    if ch.get("text"):
                        parts.append(str(ch["text"]))
                else:
                    # generic textual fallback
                    t = ch.get("text") if isinstance(ch, dict) else None
                    if t:
                        parts.append(str(t))
        return "".join(parts) if parts else None
    except Exception:
        return None


def extract_text(resp: Any) -> str:
    """Return assistant text from either Chat Completions or Responses API.
    Returns empty string if nothing is found (instead of raising).
    """
    if resp is None:
        return ""
    # Try chat.completions shape first
    text = _from_chat_completions(resp)
    if text is not None:
        return text
    # Then try responses API shape
    text = _from_responses_api(resp)
    return text or ""


def with_retry(func, max_retries: int = 3, base_delay: float = 0.6):
    """Simple retry wrapper for transient 429/5xx-like failures."""
    def _call(*args, **kwargs):
        last_err = None
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_err = e
                # naive backoff
                time.sleep(base_delay * (2 ** i))
        if last_err:
            raise last_err
        return None
    return _call
