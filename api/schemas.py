"""
api/schemas.py

Modelos de entrada para os endpoints `/estimate` e `/process`.
Campos:
- `order`: sequência global de páginas (src_id + page_index).
- `keep`: vetor booleano; páginas `False` são ignoradas.
- `rotate`: ângulos por página (0/90/180/270).
- `level_page`: níveis por página; se não vier, o backend completa com `none`.
- `level_global`: nível aplicado a todas as páginas `keep=True` se informado.
"""

# api/schemas.py
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

class OrderItem(BaseModel):
    src_id: int
    page_index: int

class EstimateIn(BaseModel):
    token: str
    order: List[OrderItem]
    keep:  List[bool]
    rotate: List[int]
    level_page: List[str]
    level_global: Optional[str] = None

class ProcessIn(EstimateIn):
    filename_out: Optional[str] = None
