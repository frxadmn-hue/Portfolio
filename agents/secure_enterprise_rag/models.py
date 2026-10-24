"""
Domain Models for On-Premise Secure RAG & PII Anonymization Guard.
Enforces Russian Federal Law 152-FZ and Commercial Trade Secret protection (98-FZ).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"                                   # Общедоступные данные
    INTERNAL = "INTERNAL"                               # Внутренние регламенты
    COMMERCIAL_SECRET = "COMMERCIAL_SECRET"             # Ноу-хау, рецептуры косметики (98-ФЗ)
    PII_RESTRICTED = "PII_RESTRICTED"                   # Персональные данные (152-ФЗ)


class DepartmentAccess(str, Enum):
    ALL = "all"
    RD_LABORATORY = "rd_laboratory"
    LEGAL = "legal"
    PROCUREMENT = "procurement"
    EXECUTIVE = "executive"


class DocumentChunk(BaseModel):
    chunk_id: str
    title: str
    text: str
    department: DepartmentAccess
    classification: DataClassification
    author: Optional[str] = None
    created_date: str = "2026-10-24"


class SanitizedChunk(BaseModel):
    chunk_id: str
    sanitized_text: str
    redaction_count: int
    contains_pii: bool
    contains_formula_secret: bool
    token_vault_keys: List[str]


class SearchQuery(BaseModel):
    query_text: str
    user_department: DepartmentAccess
    top_k: int = 3
    sanitize_for_external_llm: bool = True


class SearchResultItem(BaseModel):
    chunk_id: str
    title: str
    score: float
    text_snippet: str
    department: str
    classification: str
    is_sanitized: bool
