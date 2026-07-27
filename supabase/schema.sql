-- Schema Supabase per "Trascrivi & Riscrivi Reel".
-- Eseguire nel SQL Editor del progetto Supabase.

-- Archivio dei reel elaborati -----------------------------------------------
create table if not exists reels (
  id                  uuid primary key default gen_random_uuid(),
  source_url          text not null,
  source_lang         text,
  transcript_original text,
  transcript_it       text,
  rewritten_reel      text,
  notes               text,             -- appunti personali, indicizzati per la ricerca
  created_at          timestamptz default now(),
  -- colonna full-text generata: comoda per il client (.text_search('fts', ...))
  fts tsvector generated always as (
    to_tsvector(
      'italian',
      coalesce(transcript_it, '') || ' ' ||
      coalesce(rewritten_reel, '') || ' ' ||
      coalesce(notes, '')
    )
  ) stored
);

create index if not exists reels_fts_idx on reels using gin (fts);
create index if not exists reels_created_at_idx on reels (created_at desc);

-- Profilo brand (una riga sola, modificabile) -------------------------------
create table if not exists brand_profile (
  id      int primary key default 1,
  content text not null
);

-- Nota: il contenuto iniziale del brand (§7 del brief) viene inserito dal
-- backend al primo utilizzo se la riga non esiste. In alternativa puoi
-- inserirlo qui manualmente con un INSERT ... ON CONFLICT DO NOTHING.
