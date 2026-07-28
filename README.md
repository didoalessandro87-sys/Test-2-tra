# Trascrivi & Riscrivi Reel

App installabile sul telefono (PWA) che, dato un link a un reel di Instagram:

1. scarica l'audio, lo **trascrive** (auto-lingua) e lo **traduce in italiano**;
2. lo **riscrive come reel nel tuo tono** (profilo brand editabile);
3. salva tutto in un **archivio ricercabile** (swipe file).

Tutto su piani gratuiti. Unica spesa reale: l'API di Claude per la riscrittura (centesimi/mese).

## Architettura

```
[PWA sul telefono]  ──link──▶  [Backend FastAPI]
      │                              │
      │                        1. yt-dlp + ffmpeg → scarica audio
      │                        2. Groq Whisper → trascrizione (auto-lingua)
      │                        3. Claude API → traduzione IT + reel riscritto
      │                        4. Supabase → salva nell'archivio
      ◀──── transcript IT + reel riscritto + salvataggio ────┘
```

| Pezzo | Tecnologia | Hosting gratuito |
|---|---|---|
| Frontend PWA | Vite + React | Vercel / Netlify |
| Backend | FastAPI + yt-dlp + ffmpeg | Render / Railway |
| DB | Supabase (Postgres) | Supabase free tier |
| Trascrizione | Groq `whisper-large-v3` | free tier |
| Riscrittura | Anthropic (`claude-sonnet-4-6`) | pay-as-you-go |

## Struttura del repo

```
backend/          FastAPI: /process, /reels, /brand, /health
  app/
    main.py           orchestrazione della pipeline + endpoint
    downloader.py     yt-dlp + ffmpeg (download audio)
    transcription.py  Groq Whisper — ISOLATO (sostituibile con Whisper locale)
    rewriter.py       Anthropic (traduzione + riscrittura, output JSON)
    storage.py        Supabase (archivio + profilo brand)
  Dockerfile          include ffmpeg
frontend/         PWA React (home, archivio, impostazioni brand, share target)
  public/manifest.webmanifest   share_target verso /share
supabase/schema.sql   tabelle reels + brand_profile (con full-text italiano)
render.yaml           deploy backend su Render
```

## Setup rapido (in locale)

### 1. Supabase
- Crea un progetto su [supabase.com](https://supabase.com).
- SQL Editor → incolla ed esegui `supabase/schema.sql`.
- Copia `Project URL` e la **service_role key** (Settings → API).

### 2. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # compila GROQ/ANTHROPIC/SUPABASE
# serve ffmpeg installato: sudo apt install ffmpeg (o brew install ffmpeg)
uvicorn app.main:app --reload
```
Test da terminale con un reel pubblico:
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/reel/XXXX/"}'
```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_BASE=http://localhost:8000
npm run dev
```

## Deploy (produzione)

- **Backend → Render**: nuovo *Web Service* dal repo, `render.yaml` è già pronto
  (runtime Docker, ffmpeg incluso). Imposta le env var (chiavi Groq, Anthropic,
  Supabase, e `CORS_ORIGINS` con l'URL del frontend).
- **Frontend → Vercel**: importa il repo, root `frontend/`. Imposta
  `VITE_API_BASE` con l'URL pubblico del backend Render. `vercel.json` gestisce
  già il routing SPA (incluso `/share`).

Vedi `backend/README.md` e `frontend/README.md` per dettagli.

## Chiavi necessarie (`backend/.env`)
```
GROQ_API_KEY=...        # console.groq.com
ANTHROPIC_API_KEY=...   # console.anthropic.com
ANTHROPIC_MODEL=claude-sonnet-4-6
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
CORS_ORIGINS=*          # in prod: l'URL del frontend
```

## Note (edge case gestiti)
- **Login Instagram**: sui reel pubblici va liscio. Se IG chiede login, imposta
  `YTDLP_COOKIES_FILE` con un file cookie nel backend.
- **Reel già in italiano**: la trascrizione resta com'è, la riscrittura procede.
- **Nessun parlato**: l'app mostra "Nessun audio parlato rilevato".
- **Rate limit Groq**: messaggio pulito, basta riprovare.
- **Cold start backend**: il frontend mostra "Sto svegliando il server…".

## Cambiare motore di trascrizione
`backend/app/transcription.py` è isolato: mantieni la firma
`transcribe(audio_path) -> TranscriptionResult` e puoi sostituire Groq con
Whisper locale senza toccare il resto.
