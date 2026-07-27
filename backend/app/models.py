"""Schemi Pydantic per request/response dell'API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    url: str = Field(..., description="Link al reel di Instagram (o altra fonte supportata da yt-dlp).")
    notes: Optional[str] = Field(None, description="Appunti personali, salvati nell'archivio e indicizzati per la ricerca.")


class ProcessResponse(BaseModel):
    id: Optional[str] = None
    source_url: str
    source_lang: Optional[str] = None
    transcript_original: Optional[str] = None
    transcript_it: Optional[str] = None
    rewritten_reel: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class ReelItem(BaseModel):
    id: str
    source_url: str
    source_lang: Optional[str] = None
    transcript_original: Optional[str] = None
    transcript_it: Optional[str] = None
    rewritten_reel: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class BrandProfile(BaseModel):
    content: str


class BrandUpdate(BaseModel):
    content: str = Field(..., min_length=1)
