"""
api/storage.py

Sessões efêmeras em RAM, indexadas por `token`.
- Guarda blobs originais (`files`), nomes e `items` (metadados de páginas).
- `purge_expired()`: remove sessões antigas (TTL em minutos via `TTL_MINUTES`).
"""

from __future__ import annotations
import time, secrets
from typing import Dict, List

TTL_MIN = int(__import__("os").getenv("TTL_MINUTES", "15"))

class Session:
    """Guarda blobs originais e a lista de páginas para reuso nos próximos passos."""
    def __init__(self, files: List[bytes], names: List[str], items: List[dict]):
        self.files = files
        self.names = names
        self.items = items
        self.created_at = time.time()

SESSIONS: Dict[str, Session] = {}  # token -> Session

def new_token() -> str:
    return secrets.token_urlsafe(16)

def purge_expired() -> None:
    now = time.time()
    ttl = TTL_MIN * 60
    for k in list(SESSIONS.keys()):
        if now - SESSIONS[k].created_at > ttl:
            SESSIONS.pop(k, None)
