"""Modulo di trascrizione — ISOLATO di proposito.

Oggi usa Groq (whisper-large-v3). Domani puoi sostituire l'implementazione di
`transcribe(audio_path)` con Whisper locale senza toccare il resto dell'app:
basta mantenere la stessa firma e lo stesso `TranscriptionResult`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from groq import Groq

from .config import get_settings


class TranscriptionError(RuntimeError):
    pass


@dataclass
class TranscriptionResult:
    text: str
    language: Optional[str] = None


def transcribe(audio_path: str) -> TranscriptionResult:
    """Trascrive l'audio con auto-rilevamento della lingua.

    Ritorna testo (eventualmente vuoto se non c'è parlato) e lingua rilevata.
    """
    settings = get_settings()
    if not settings.groq_api_key:
        raise TranscriptionError("GROQ_API_KEY non configurata.")

    client = Groq(api_key=settings.groq_api_key)

    try:
        with open(audio_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=(audio_path, f.read()),
                model=settings.groq_whisper_model,
                # verbose_json ci dà anche la lingua rilevata
                response_format="verbose_json",
            )
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "rate" in msg and "limit" in msg:
            raise TranscriptionError(
                "Limite di richieste Groq raggiunto. Riprova tra poco."
            ) from exc
        raise TranscriptionError(f"Errore di trascrizione: {exc}") from exc

    text = (getattr(resp, "text", "") or "").strip()
    language = getattr(resp, "language", None)
    return TranscriptionResult(text=text, language=language)
