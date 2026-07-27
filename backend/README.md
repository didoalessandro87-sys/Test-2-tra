# Backend — Trascrivi & Riscrivi Reel

FastAPI. Pipeline: **download audio → trascrizione → riscrittura → salvataggio**.

## Endpoint

| Metodo | Path | Descrizione |
|---|---|---|
| `GET`  | `/health` | Stato + quali servizi sono configurati |
| `POST` | `/process` | `{ "url": "...", "notes": "opz" }` → JSON risultato |
| `GET`  | `/reels?q=` | Lista archivio, con ricerca full-text opzionale |
| `GET`  | `/reels/{id}` | Dettaglio di un reel |
| `GET`  | `/brand` | Profilo brand corrente (default se non salvato) |
| `PUT`  | `/brand` | `{ "content": "..." }` aggiorna il profilo brand |

## Esecuzione locale
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # compila le chiavi
uvicorn app.main:app --reload
```
Richiede **ffmpeg** installato nel sistema (yt-dlp lo usa per estrarre l'audio).

## Variabili d'ambiente
Vedi `.env.example`. Minime per un test end-to-end: `GROQ_API_KEY`,
`ANTHROPIC_API_KEY`. Senza Supabase l'app funziona lo stesso ma **non salva**
in archivio e usa il brand di default.

## Deploy su Render
Il `render.yaml` nella root usa il `Dockerfile` (ffmpeg incluso). In alternativa,
crea un Web Service Docker puntando a `backend/`.

## Moduli
- `downloader.py` — yt-dlp + ffmpeg. Gestisce login-richiesto e link non validi.
- `transcription.py` — **isolato**: Groq Whisper oggi, sostituibile con Whisper
  locale mantenendo `transcribe(path) -> TranscriptionResult`.
- `rewriter.py` — Anthropic. Usa structured outputs per un JSON sempre valido,
  con fallback a parsing robusto.
- `storage.py` — Supabase (archivio + brand). Degrada con grazia se non configurato.
