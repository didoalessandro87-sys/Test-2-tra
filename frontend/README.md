# Frontend — Trascrivi & Riscrivi Reel (PWA)

Vite + React. Installabile sul telefono, con **Web Share Target** per ricevere
il link condiviso da Instagram.

## Schermate
- **Home** (`/`): incolla il link + "Elabora", stato di avanzamento, risultato
  (trascritto IT + reel riscritto) con pulsanti copia. Salvataggio automatico.
- **Archivio** (`/archive`): lista dei reel elaborati, con ricerca full-text.
- **Brand** (`/settings`): modifica il profilo brand usato nella riscrittura.
- **Share** (`/share`): rotta del share target; estrae il primo URL da
  `url`/`text`/`title` e avvia l'elaborazione in automatico.

## Esecuzione locale
```bash
npm install
cp .env.example .env    # VITE_API_BASE=http://localhost:8000
npm run dev
```

## Build
```bash
npm run build           # output in dist/
```

## Deploy su Vercel
- Importa il repo, imposta **Root Directory** = `frontend`.
- Env var: `VITE_API_BASE` = URL pubblico del backend.
- `vercel.json` gestisce il routing SPA (necessario per `/share`, `/archive`).
- Su Netlify il file `public/_redirects` fa lo stesso.

## Web Share Target
Definito in `public/manifest.webmanifest`:
```json
"share_target": { "action": "/share", "method": "GET",
  "params": { "url": "url", "text": "text", "title": "title" } }
```
Installa la PWA sulla home del telefono, poi da Instagram usa "Condividi →
Trascrivi Reel": il link arriva a `/share`, viene estratto e l'elaborazione parte.

> Nota: il share target funziona solo con la PWA **installata** e servita in
> **HTTPS** (Vercel/Netlify lo sono).
