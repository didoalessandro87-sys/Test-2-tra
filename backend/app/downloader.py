"""Download dell'audio da un link (Instagram reel, ecc.) tramite yt-dlp + ffmpeg.

Isolato dal resto: espone solo `download_audio(url) -> DownloadedAudio`.
"""
from __future__ import annotations

import os
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

    def cleanup(self) -> None:
        try:
            os.remove(self.path)
        except OSError:
            pass


def download_audio(url: str) -> DownloadedAudio:
    """Scarica solo la traccia audio del reel e la converte in mp3.

    Solleva DownloadError con un messaggio pulito in caso di problemi
    (link non valido, contenuto privato/login richiesto, nessun media).
    """
    settings = get_settings()
    tmpdir = tempfile.mkdtemp(prefix="reel_")
    outtmpl = str(Path(tmpdir) / "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    cookies_file = settings.ytdlp_cookies_file.strip()
    if cookies_file and Path(cookies_file).is_file():
        ydl_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as exc:  # noqa: BLE001 — yt-dlp solleva vari tipi
        msg = str(exc).lower()
        if "login" in msg or "rate-limit" in msg or "private" in msg or "cookies" in msg:
            raise DownloadError(
                "Instagram ha richiesto il login per questo contenuto. "
                "Configura un file cookie (YTDLP_COOKIES_FILE) nel backend."
            ) from exc
        raise DownloadError(f"Impossibile scaricare l'audio dal link: {exc}") from exc

    # Dopo la post-elaborazione il file è audio.mp3
    audio_path = str(Path(tmpdir) / "audio.mp3")
    if not Path(audio_path).is_file():
        # fallback: prendi il primo file nella cartella
        files = list(Path(tmpdir).glob("audio.*"))
        if not files:
            raise DownloadError("Download completato ma nessun file audio trovato.")
        audio_path = str(files[0])

    title = None
    duration = None
    if isinstance(info, dict):
        title = info.get("title")
        duration = info.get("duration")

    return DownloadedAudio(path=audio_path, title=title, duration=duration)
