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
