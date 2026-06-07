-- YT DARK v2 — tabela canais + coluna aprovado em canais_candidatos

CREATE TABLE IF NOT EXISTS canais (
    id          bigserial PRIMARY KEY,
    canal_id    text    NOT NULL UNIQUE,
    handle      text    NOT NULL,
    nome        text    NOT NULL,
    ativo       boolean NOT NULL DEFAULT true,
    config_json jsonb   NOT NULL DEFAULT '{}',
    dna_json    jsonb   NOT NULL DEFAULT '{}',
    created_at  timestamptz DEFAULT now()
);

ALTER TABLE canais_candidatos
    ADD COLUMN IF NOT EXISTS aprovado boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_canais_candidatos_aprovado
    ON canais_candidatos(canal_id, aprovado);

CREATE INDEX IF NOT EXISTS idx_videos_status
    ON videos(canal_id, status);

-- Seed: canal mofmoney
INSERT INTO canais (canal_id, handle, nome, config_json, dna_json)
VALUES (
    'mofmoney',
    '@mofmoney',
    'MofMoney',
    '{
        "youtube_handle": "@mofmoney",
        "idioma": "en",
        "nicho_keywords": ["personal finance", "investing", "passive income"],
        "canais_fonte": ["@CasuallyFinance", "@nickinvestsUS"],
        "tipo_video_padrao": "whiteboard",
        "filtros_mineracao": {
            "min_views": 50000,
            "max_dias": 30,
            "duracao_min_min": 8,
            "duracao_max_min": 20
        }
    }',
    '{
        "estilo_visual": "whiteboard",
        "tom_voz": "casual and educational",
        "paleta_cores": ["#FF6B35", "#FFFFFF", "#2C3E50"],
        "titulo_formula": "[Number] Ways to [Benefit] (No [Common Excuse])",
        "duracao_alvo_min": 12
    }'
)
ON CONFLICT (canal_id) DO NOTHING;
