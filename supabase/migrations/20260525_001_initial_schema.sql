-- YT DARK — schema inicial
-- Tabela de vídeos minerados por canal

CREATE TABLE IF NOT EXISTS videos (
    id          bigserial PRIMARY KEY,
    canal_id    text      NOT NULL,
    video_id    text      NOT NULL,
    titulo      text      NOT NULL,
    canal_fonte text      NOT NULL,
    views       integer   NOT NULL DEFAULT 0,
    data_pub    text      NOT NULL,
    duracao_min float     NOT NULL DEFAULT 0,
    tipo        text      NOT NULL DEFAULT 'whiteboard',
    score       float     NOT NULL DEFAULT 0,
    status      text      NOT NULL DEFAULT 'candidato',
    transcricao text,
    analise     jsonb,
    roteiro_path    text,
    audio_path      text,
    thumbnail_path  text,
    video_path      text,
    drive_link      text,
    yt_link         text,
    created_at  timestamptz DEFAULT now(),
    UNIQUE (canal_id, video_id)
);

-- Canais candidatos descobertos na fase de descoberta

CREATE TABLE IF NOT EXISTS canais_candidatos (
    id                  bigserial PRIMARY KEY,
    canal_id            text    NOT NULL,
    handle              text    NOT NULL,
    nome                text    NOT NULL,
    channel_id          text    NOT NULL,
    subscribers         integer NOT NULL DEFAULT 0,
    avg_views           float   NOT NULL DEFAULT 0,
    engagement_rate     float   NOT NULL DEFAULT 0,
    upload_freq_mensal  float   NOT NULL DEFAULT 0,
    avg_duration_min    float   NOT NULL DEFAULT 0,
    momentum            text    NOT NULL DEFAULT 'estavel',
    score               float   NOT NULL DEFAULT 0,
    melhor_video_recente jsonb,
    adicionado          boolean NOT NULL DEFAULT false,
    created_at          timestamptz DEFAULT now(),
    UNIQUE (canal_id, handle)
);

-- Keywords pesquisadas por canal

CREATE TABLE IF NOT EXISTS keywords (
    id          bigserial PRIMARY KEY,
    canal_id    text    NOT NULL,
    termo       text    NOT NULL,
    volume      integer NOT NULL DEFAULT 0,
    competition float   NOT NULL DEFAULT 0,
    seo_score   float   NOT NULL DEFAULT 0,
    data        text,
    created_at  timestamptz DEFAULT now(),
    UNIQUE (canal_id, termo)
);

-- RLS: desabilitado por padrão (acesso via service_role key no backend)
-- Para habilitar, execute:
-- ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE canais_candidatos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
