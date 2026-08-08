"""Download dell'audio da un link (Instagram reel, ecc.) tramite yt-dlp + ffmpeg.

Isolato dal resto: espone solo `download_audio(url) -> DownloadedAudio`.

Strategia a due tentativi:
  Tentativo 1 (strada principale, affidabile per i reel normali):
      yt-dlp scarica `bestaudio/best` ed estrae l'audio in mp3 con il suo
      post-processore (FFmpegExtractAudio).
  Tentativo 2 (piano B per i reel "ostici", solo se il 1 fallisce):
      scarica il video completo (video+audio, uniti se separati) e ne estraiamo
      noi l'audio con una chiamata diretta a ffmpeg. Se anche la conversione
      fallisce, passiamo il file grezzo alla trascrizione (Groq accetta mp4/m4a).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
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


def _looks_like_login(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("login", "rate-limit", "private", "cookies", "sign in", "log in"))


_COOKIES_TMP: Optional[str] = None


def _cookies_path() -> Optional[str]:
    """Percorso a un file cookies.txt, da file esplicito o dal contenuto in env.

    Su Render è comodo incollare il contenuto del cookies.txt nella variabile
    YTDLP_COOKIES_CONTENT: qui lo scriviamo una volta in un file temporaneo.
    """
    global _COOKIES_TMP
    settings = get_settings()

    explicit = settings.ytdlp_cookies_file.strip()
    if explicit and Path(explicit).is_file():
        return explicit

    content = settings.ytdlp_cookies_content.strip()
    if content:
        if _COOKIES_TMP and Path(_COOKIES_TMP).is_file():
            return _COOKIES_TMP
        path = Path(tempfile.gettempdir()) / "ig_cookies.txt"
        path.write_text(content + "\n", encoding="utf-8")
        _COOKIES_TMP = str(path)
        return _COOKIES_TMP
    return None


def _base_opts() -> dict:
    opts = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    cookies = _cookies_path()
    if cookies:
        opts["cookiefile"] = cookies
    return opts


def _run(url: str, tmpdir: str, extra: dict) -> dict:
    outtmpl = str(Path(tmpdir) / "audio.%(ext)s")
    ydl_opts = {**_base_opts(), "outtmpl": outtmpl, **extra}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info if isinstance(info, dict) else {}


def _convert_to_mp3(src: str, dst: str) -> bool:
    """Estrae/riconverte l'audio di `src` in un mp3 mono 16kHz (ideale per Whisper)."""
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
    except Exception:  # noqa: BLE001
        return False
    out = Path(dst)
    return out.is_file() and out.stat().st_size > 0


def _has_audio_stream(path: str) -> bool:
    """True se il file ha almeno una traccia audio (via ffprobe).

    In caso di dubbio (ffprobe assente o errore) ritorna True per non bloccare.
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return True
    try:
        res = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_streams", path],
            check=True,
            capture_output=True,
            timeout=60,
        )
        data = json.loads(res.stdout or b"{}")
        return any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    except Exception:  # noqa: BLE001
        return True


def _first_audio_file(tmpdir: str) -> Optional[Path]:
    files = sorted(Path(tmpdir).glob("audio.*"))
    return files[0] if files else None


# Errori "intermittenti" tipici del server anonimo throttlato da Instagram:
# spesso al 2°/3° tentativo la richiesta passa. NON riproviamo i casi "login"
# (persistenti: si risolvono coi cookie, non riprovando).
_RETRIABLE = (
    "nessuna traccia audio",
    "nessun file",
    "non ha restituito",
    "impossibile scaricare",
)


def download_audio(url: str) -> DownloadedAudio:
    """Wrapper con riprova automatica sugli errori intermittenti di Instagram."""
    attempts = 3
    last_exc: Optional[DownloadError] = None
    for i in range(attempts):
        try:
            return _download_pipeline(url)
        except DownloadError as exc:
            last_exc = exc
            msg = str(exc).lower()
            retriable = any(k in msg for k in _RETRIABLE)
            if not retriable or i == attempts - 1:
                raise
            time.sleep(1.5 * (i + 1))  # piccola pausa crescente prima di riprovare
    assert last_exc is not None
    raise last_exc


def _download_pipeline(url: str) -> DownloadedAudio:
    """Scarica la traccia audio del reel e la prepara per la trascrizione."""
    # ---- Tentativo 1: estrazione audio "classica" di yt-dlp (affidabile) -----
    t1 = tempfile.mkdtemp(prefix="reel1_")
    try:
        info = _run(
            url,
            t1,
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
                ],
            },
        )
        mp3 = Path(t1) / "audio.mp3"
        if mp3.is_file() and mp3.stat().st_size > 1024:
            return DownloadedAudio(
                path=str(mp3),
                title=info.get("title"),
                duration=info.get("duration"),
                _tmpdir=t1,
            )
    except Exception as exc:  # noqa: BLE001
        if _looks_like_login(exc):
            shutil.rmtree(t1, ignore_errors=True)
            raise DownloadError(
                "Instagram ha richiesto il login per questo contenuto. "
                "Configura un file cookie (YTDLP_COOKIES_FILE) nel backend."
            ) from exc
        # altrimenti: passa al piano B
    shutil.rmtree(t1, ignore_errors=True)

    # ---- Tentativo 2: video completo + estrazione audio "a mano" -------------
    t2 = tempfile.mkdtemp(prefix="reel2_")
    try:
        info = _run(
            url,
            t2,
            {
                # default "intelligente" di yt-dlp: video+audio (uniti se separati)
                "format": "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
            },
        )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(t2, ignore_errors=True)
        if _looks_like_login(exc):
            raise DownloadError(
                "Instagram ha richiesto il login per questo contenuto. "
                "Configura un file cookie (YTDLP_COOKIES_FILE) nel backend."
            ) from exc
        raise DownloadError(f"Impossibile scaricare l'audio dal link: {exc}") from exc

    raw = _first_audio_file(t2)
    if raw is None:
        shutil.rmtree(t2, ignore_errors=True)
        raise DownloadError("Download completato ma nessun file trovato.")
    if raw.stat().st_size < 1024:
        shutil.rmtree(t2, ignore_errors=True)
        raise DownloadError(
            "Instagram non ha restituito il contenuto (forse privato o non "
            "disponibile senza login)."
        )

    # Il reel non ha proprio audio? Messaggio chiaro invece dell'errore di Groq.
    if not _has_audio_stream(str(raw)):
        shutil.rmtree(t2, ignore_errors=True)
        raise DownloadError("Nessuna traccia audio nel reel (video senza sonoro).")

    mp3 = str(Path(t2) / "converted.mp3")
    audio_path = mp3 if _convert_to_mp3(str(raw), mp3) else str(raw)

    return DownloadedAudio(
        path=audio_path,
        title=info.get("title"),
        duration=info.get("duration"),
        _tmpdir=t2,
    )
