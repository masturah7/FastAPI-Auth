import hashlib
import threading
import time
from typing import Any

_cache: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()
DEFAULT_TTL = 60


def make_key(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()


def get(key: str):
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        if entry["expires"] < time.time():
            del _cache[key]
            return None
        return entry["value"]


def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    with _lock:
        _cache[key] = {"value": value, "expires": time.time() + ttl}


def clear() -> None:
    with _lock:
        _cache.clear()


def ai_generate(prompt: str):
    """Return (result, cached) for a (mock) AI response, caching non-sensitive results."""
    key = make_key("ai", prompt)
    cached = get(key)
    if cached is not None:
        return cached, True
    # Mock AI response - replace with real model call in production.
    result = f"Assistant: {prompt.strip()}"
    set(key, result)
    return result, False
