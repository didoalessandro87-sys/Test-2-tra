"""Download dell'audio da un link (Instagram reel, ecc.) tramite yt-dlp + ffmpeg.

Isolato dal resto: espone solo `download_audio(url) -> DownloadedAudio`.

Strategia robusta:
1. yt-dlp scarica la traccia audio grezza (senza post-processing fragile).
2. La convertiamo noi in mp3 con una chiamata diretta a ffmpeg (tollerante).
3. Se ffmpeg non ce la fa, passiamo comunque il file grezzo alla trascrizione
   (Groq accetta m4a/webm/mp4/ogg ecc.).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from yt_dlp import YoutubeDL

from .config import get_settings


class DownloadError(RuntimeError):
    """Errore durante il download dell'audio (link privato, login richiesto, ecc.)."""


@dataclass
class DownloadedAudio:
    path: str
    title: Optional[str]
    duration: Optional[float]
    _tmpdir: Optional[str] = None

    def cleanup(self) -> None:
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)


def _convert_to_mp3(src: str, dst: str) -> bool:
    """Converte `src` in un mp3 mono 16kHz (ottimo per Whisper) con ffmpeg.

    Ritorna True se l'output è stato creato correttamente, False altrimenti.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "96k", dst],
            check=True,
            capture_output=True,
            timeout=240,
        )
    except Exception:  # noqa: BLE001 — qualsiasi problema ffmpeg -> fallback
        return False
    out = Path(dst)
    return out.is_file() and out.stat().st_size > 0


def download_audio(url: str) -> DownloadedAudio:
    """Scarica la traccia audio del reel e la prepara per la trascrizione.

    Solleva DownloadError con un messaggio pulito in caso di problemi
    (link non valido, contenuto privato/login richiesto, nessun media).
    """
    settings = get_settings()
    tmpdir = tempfile.mkdtemp(prefix="reel_")
    outtmpl = str(Path(tmpdir) / "audio.%(ext)s")

    ydl_opts = {
        # Sceglie SOLO formati che contengono davvero una traccia audio
        # (evita flussi video-only che poi darebbero "no audio track").
        "format": "bestaudio[acodec!=none]/best[acodec!=none]/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    cookies_file = settings.ytdlp_cookies_file.strip()
    if cookies_file and Path(cookies_file).is_file():
        ydl_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as exc:  # noqa: BLE001 — yt-dlp solleva vari tipi
        shutil.rmtree(tmpdir, ignore_errors=True)
        msg = str(exc).lower()
        if "login" in msg or "rate-limit" in msg or "private" in msg or "cookies" in msg:
            raise DownloadError(
                "Instagram ha richiesto il login per questo contenuto. "
                "Configura un file cookie (YTDLP_COOKIES_FILE) nel backend."
            ) from exc
        raise DownloadError(f"Impossibile scaricare l'audio dal link: {exc}") from exc

    # Individua il file scaricato (estensione variabile: m4a/webm/mp4/...)
    files = sorted(Path(tmpdir).glob("audio.*"))
    if not files:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise DownloadError("Download completato ma nessun file audio trovato.")
    raw = files[0]

    # Un file minuscolo di solito significa contenuto bloccato (login/anteprima)
    if raw.stat().st_size < 1024:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise DownloadError(
            "Instagram non ha restituito l'audio (contenuto forse privato o non "
            "disponibile senza login)."
        )

    # Prova a convertire in mp3; se fallisce usa il file grezzo (Groq lo accetta)
    mp3 = str(Path(tmpdir) / "converted.mp3")
    audio_path = mp3 if _convert_to_mp3(str(raw), mp3) else str(raw)

    title = None
    duration = None
    if isinstance(info, dict):
        title = info.get("title")
        duration = info.get("duration")

    return DownloadedAudio(path=audio_path, title=title, duration=duration, _tmpdir=tmpdir)
