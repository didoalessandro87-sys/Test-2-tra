"""FastAPI app: orchestrazione download -> trascrizione -> riscrittura -> archivio."""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import storage
from .config import get_settings
from .downloader import DownloadError, download_audio
from .models import (
    BrandProfile,
    BrandUpdate,
    ProcessRequest,
    ProcessResponse,
    ReelItem,
)
from .rewriter import RewriteError, rewrite
from .transcription import TranscriptionError, transcribe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trascrivi-reel")

settings = get_settings()

app = FastAPI(title="Trascrivi & Riscrivi Reel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "supabase": storage.is_configured(),
        "groq": bool(settings.groq_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "model": settings.anthropic_model,
    }


@app.post("/process", response_model=ProcessResponse)
def process(req: ProcessRequest) -> ProcessResponse:
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL mancante.")

    # 1) Download audio
    try:
        audio = download_audio(url)
    except DownloadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        # 2) Trascrizione (auto-lingua)
        try:
            tr = transcribe(audio.path)
        except TranscriptionError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        if not tr.text:
            raise HTTPException(
                status_code=422,
                detail="Nessun audio parlato rilevato nel reel.",
            )

        # 3) Riscrittura + traduzione
        brand_prompt = storage.get_brand()
        try:
            rw = rewrite(brand_prompt, tr.text, source_lang=tr.language)
        except RewriteError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        # 4) Salvataggio in archivio (best-effort)
        saved = None
        try:
            saved = storage.save_reel(
                source_url=url,
                source_lang=tr.language,
                transcript_original=tr.text,
                transcript_it=rw.transcript_it,
                rewritten_reel=rw.rewritten_reel,
                notes=(req.notes or None),
            )
        except Exception as exc:  # noqa: BLE001 — non bloccare l'utente se il salvataggio fallisce
            logger.warning("Salvataggio archivio fallito: %s", exc)

        return ProcessResponse(
            id=(saved or {}).get("id"),
            source_url=url,
            source_lang=tr.language,
            transcript_original=tr.text,
            transcript_it=rw.transcript_it,
            rewritten_reel=rw.rewritten_reel,
            notes=req.notes,
            created_at=(saved or {}).get("created_at"),
        )
    finally:
        audio.cleanup()


@app.get("/reels", response_model=list[ReelItem])
def reels(q: str | None = None) -> list[ReelItem]:
    rows = storage.list_reels(query=q)
    return [ReelItem(**r) for r in rows]


@app.get("/reels/{reel_id}", response_model=ReelItem)
def reel_detail(reel_id: str) -> ReelItem:
    row = storage.get_reel(reel_id)
    if not row:
        raise HTTPException(status_code=404, detail="Reel non trovato.")
    return ReelItem(**row)


@app.get("/brand", response_model=BrandProfile)
def brand() -> BrandProfile:
    return BrandProfile(content=storage.get_brand())


@app.put("/brand", response_model=BrandProfile)
def brand_update(body: BrandUpdate) -> BrandProfile:
    try:
        content = storage.update_brand(body.content)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return BrandProfile(content=content)
