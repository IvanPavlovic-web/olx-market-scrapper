import itertools
import threading
import time
from typing import Optional


class ProxyPool:
    def __init__(self, proxies: list[str], rotate_interval: int = 60):
        self._proxies = list(proxies)
        self._cycle = itertools.cycle(self._proxies) if self._proxies else None
        self._lock = threading.Lock()
        self._bad_until: dict[str, float] = {}

    def get(self) -> Optional[str]:
        if not self._cycle:
            return None
        with self._lock:
            for _ in range(len(self._proxies)):
                p = next(self._cycle)
                if self._bad_until.get(p, 0) < time.time():
                    return p
            return self._proxies[0]

    def mark_bad(self, proxy: str, cooldown: int = 300) -> None:
        with self._lock:
            self._bad_until[proxy] = time.time() + cooldown

    def mark_good(self, proxy: str) -> None:
        pass
