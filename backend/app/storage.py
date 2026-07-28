"""Integrazione Supabase: archivio reel + profilo brand.

Se Supabase non e configurato, l'app continua a funzionare (elaborazione
senza salvataggio) e usa il brand di default: comodo per i primi test locali.
"""
from __future__ import annotations

from typing import Any, Optional

from supabase import Client, create_client

from .brand_default import DEFAULT_BRAND
from .config import get_settings

_client: Optional[Client] = None


def _get_client() -> Optional[Client]:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def is_configured() -> bool:
    return _get_client() is not None


# ---------------------------------------------------------------------------
# Brand profile
# ---------------------------------------------------------------------------

def get_brand() -> str:
    client = _get_client()
    if client is None:
        return DEFAULT_BRAND
    try:
        res = client.table("brand_profile").select("content").eq("id", 1).limit(1).execute()
        rows = res.data or []
        if rows and rows[0].get("content"):
            return rows[0]["content"]
    except Exception:  # noqa: BLE001 — tabella mancante o rete: usa il default
        pass
    return DEFAULT_BRAND


def update_brand(content: str) -> str:
    client = _get_client()
    if client is None:
        raise StorageError("Supabase non configurato: impossibile salvare il brand.")
    client.table("brand_profile").upsert({"id": 1, "content": content}).execute()
    return content


# ---------------------------------------------------------------------------
# Reel archive
# ---------------------------------------------------------------------------

def save_reel(
    *,
    source_url: str,
    source_lang: Optional[str],
    transcript_original: Optional[str],
    transcript_it: Optional[str],
    rewritten_reel: Optional[str],
    notes: Optional[str],
) -> Optional[dict[str, Any]]:
    client = _get_client()
    if client is None:
        return None
    payload = {
        "source_url": source_url,
        "source_lang": source_lang,
        "transcript_original": transcript_original,
        "transcript_it": transcript_it,
        "rewritten_reel": rewritten_reel,
        "notes": notes,
    }
    res = client.table("reels").insert(payload).execute()
    rows = res.data or []
    return rows[0] if rows else None


def list_reels(query: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
    client = _get_client()
    if client is None:
        return []
    q = query.strip() if query else ""
    table = client.table("reels")
    if q:
        try:
            res = (
                table.select("*")
                .text_search("fts", q, options={"type": "websearch", "config": "italian"})
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception:  # noqa: BLE001 — fallback a ricerca semplice
            like = f"%{q}%"
            res = (
                table.select("*")
                .or_(
                    f"transcript_it.ilike.{like},"
                    f"rewritten_reel.ilike.{like},"
                    f"notes.ilike.{like}"
                )
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
    res = table.select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data or []


def get_reel(reel_id: str) -> Optional[dict[str, Any]]:
    client = _get_client()
    if client is None:
        return None
    res = client.table("reels").select("*").eq("id", reel_id).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else None


class StorageError(RuntimeError):
    pass
