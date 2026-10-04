from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


class C:
    def __init__(self, now: Callable[[], float] = time.time) -> None:
        self._now = now
        self.ttl = 100

    def _load(self) -> dict[str, dict]:
        return {}

    def __contains__(self, key: str) -> bool:
        entry = self._load().get(key)
        if entry is None:
            return False
        return self._now() - float(entry["ts"]) <= self.ttl


def g() -> Any: ...


def f() -> dict[str, Any] | None:
    info: dict[str, Any] | None = g()
    if info is None:
        return None
    return info


def k() -> str:
    response: str = g()
    return response
