"""
api/jobs.py

Armazena artefatos finais (PDFs) em memória por tempo limitado (TTL).
- `save_job(data, filename) -> job_id`: salva bytes e retorna um identificador.
- `pop_job(job_id) -> (bytes, filename)`: retorna e apaga (one-time download).
- `purge_expired_jobs()`: remove itens que ultrapassaram o TTL.
"""

# api/jobs.py
from __future__ import annotations
import os, time, secrets
from typing import Dict, Tuple

TTL_MIN = int(os.getenv("TTL_MINUTES", "15"))

# job_id -> (pdf_bytes, created_at_ts, filename)
JOBS: Dict[str, Tuple[bytes, float, str]] = {}

def new_job_id() -> str:
    return secrets.token_urlsafe(12)

def save_job(data: bytes, filename: str) -> str:
    job_id = new_job_id()
    JOBS[job_id] = (data, time.time(), filename)
    return job_id

def pop_job(job_id: str) -> Tuple[bytes, str] | None:
    item = JOBS.pop(job_id, None)
    if not item:
        return None
    data, _, fname = item
    return data, fname

def purge_expired_jobs() -> None:
    now = time.time()
    ttl = TTL_MIN * 60
    for k in list(JOBS.keys()):
        if now - JOBS[k][1] > ttl:
            JOBS.pop(k, None)
