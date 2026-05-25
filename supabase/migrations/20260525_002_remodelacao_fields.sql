-- Migration: adiciona campos do pipeline de remodelação na tabela videos.

ALTER TABLE videos
  ADD COLUMN IF NOT EXISTS transcricao       TEXT,
  ADD COLUMN IF NOT EXISTS prompt_titulo     TEXT,
  ADD COLUMN IF NOT EXISTS estrutura_video   TEXT,
  ADD COLUMN IF NOT EXISTS estrutura_thumb   TEXT,
  ADD COLUMN IF NOT EXISTS roteiro           TEXT,
  ADD COLUMN IF NOT EXISTS audio_path        TEXT,
  ADD COLUMN IF NOT EXISTS thumbnail_path    TEXT,
  ADD COLUMN IF NOT EXISTS video_path        TEXT,
  ADD COLUMN IF NOT EXISTS yt_link           TEXT,
  ADD COLUMN IF NOT EXISTS descricao_seo     TEXT,
  ADD COLUMN IF NOT EXISTS tags_seo          TEXT[];

CREATE INDEX IF NOT EXISTS idx_videos_canal_status ON videos(canal_id, status);
