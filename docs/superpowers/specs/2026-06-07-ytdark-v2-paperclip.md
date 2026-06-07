# YT DARK v2 — Paperclip + MCP Architecture

**Data:** 2026-06-07
**Status:** Aprovado
**Modo:** YOLO (execução autônoma)

---

## Visão Geral

Reconstrução completa do YT DARK sobre Paperclip como plataforma de orquestração central. O FastAPI e o frontend Next.js são eliminados. Os agentes Claude Code do Paperclip executam o pipeline de produção de vídeos de forma autônoma, com approval gates nas etapas críticas.

---

## O que é eliminado

```
app/                  FastAPI backend completo
frontend/             Next.js + Cloudflare Pages
Dockerfile
docker-compose.yml    (será recriado para Paperclip)
requirements.txt      (será recriado para MCP server)
check_*.py
deploy*.py
push_backend.py
force_restart.py
fix_credentials.py
setup_vps.py
redeploy_stack.py
test_login.py
pytest.ini
```

## O que é mantido

```
canais/mofmoney/config.json
canais/mofmoney/channel_dna.json
credentials/google_credentials.json
supabase/migrations/
templates/            Shotstack templates
docs/
```

---

## Nova Estrutura

```
YT DARK/
├── mcp-server/
│   ├── main.py
│   ├── tools/
│   │   ├── downloader.py    yt-dlp wrapper
│   │   ├── transcriber.py   Whisper wrapper
│   │   └── frames.py        ffmpeg wrapper
│   └── requirements.txt
├── docker-compose.yml        Paperclip + PostgreSQL
├── canais/
│   └── mofmoney/
│       ├── config.json
│       └── channel_dna.json
├── supabase/
│   └── migrations/
├── templates/
└── docs/
```

---

## Arquitetura

```
┌─────────────────────────────────────────┐
│           PAPERCLIP (Docker, VPS)        │
│                                          │
│  Company: mofmoney                       │
│  Goal: 4 vídeos/semana · finanças · EN   │
│                                          │
│  Agentes Claude Code:                    │
│  ├── Descoberta   (routine: seg 9h)      │
│  ├── Minerador    (routine: diária 8h)   │
│  ├── Analisador   (trigger: aprovação)   │
│  ├── Produtor     (trigger: análise)     │
│  └── Publicador   (trigger: aprovação)   │
└──────────────┬──────────────────────────┘
               │ MCP calls
    ┌──────────┴───────────┐
    │                      │
┌───▼──────────┐   ┌───────▼──────┐
│ ytdark-tools │   │   Supabase   │
│  MCP Server  │   │  MCP oficial │
│              │   │              │
│ download_    │   │ videos       │
│  video()     │   │ canais_cand. │
│ extract_     │   │ keywords     │
│  frames()    │   │ canais       │
│ transcribe() │   │              │
└──────────────┘   └──────────────┘
    VPS local          Cloud
```

---

## Pipeline e Approval Gates

### Agent: Descoberta
- **Trigger:** Routine toda segunda 9h
- **Executa:** YouTube Data API → ranqueia canais candidatos por métricas
- **Persiste:** `canais_candidatos` no Supabase
- **Output:** Notificação com lista ranqueada
- **Gate:** Nenhum — roda 100% autônomo

### Agent: Minerador
- **Trigger:** Routine todo dia 8h
- **Executa:** YouTube API → vídeos dos canais aprovados → score ponderado
- **Persiste:** `videos` (status=candidato) no Supabase
- **⏸️ APPROVAL GATE #1:** Você aprova quais vídeos avançar para produção

### Agent: Analisador
- **Trigger:** Vídeo com status=aprovado no Supabase
- **Executa:** `download_video` + `extract_frames` + `transcribe` + GPT-4o Vision
- **Persiste:** `videos` (status=analisado, analysis_json) no Supabase
- **Gate:** Nenhum — roda 100% autônomo

### Agent: Produtor
- **Trigger:** Vídeo com status=analisado
- **Executa:** GPT-4o (roteiro) + DALL-E 3 (thumbnail) + ElevenLabs (áudio) + Shotstack (vídeo)
- **Persiste:** `videos` (status=pronto, links Drive) no Supabase
- **⏸️ APPROVAL GATE #2:** Você revisa o vídeo final antes de publicar

### Agent: Publicador
- **Trigger:** Vídeo com status=aprovado_publicacao
- **Executa:** YouTube Data API upload
- **Persiste:** `videos` (status=publicado, yt_link) no Supabase
- **Gate:** Nenhum — roda após aprovação

---

## MCP Servers

### ytdark-tools (custom)
```python
Tools expostos:
  download_video(url: str, output_dir: str) -> dict
  extract_frames(video_path: str, n_frames: int) -> list[str]
  transcribe(video_path: str, language: str = "en") -> str
```

### supabase (oficial)
Plug-and-play. Configurado no workspace do Paperclip com SUPABASE_URL + SUPABASE_KEY.

---

## Supabase Schema (expandido)

### Tabela `videos` — novas colunas
```sql
canal_id        TEXT NOT NULL
analysis_json   TEXT
roteiro_url     TEXT
audio_url       TEXT
thumbnail_url   TEXT
video_url       TEXT
yt_link         TEXT
```

### Tabela `canais_candidatos` — novas colunas
```sql
canal_id        TEXT NOT NULL
aprovado        BOOLEAN DEFAULT false
adicionado      BOOLEAN DEFAULT false
```

### Tabela `canais` (nova)
```sql
id              UUID PRIMARY KEY
handle          TEXT NOT NULL
nome            TEXT
ativo           BOOLEAN DEFAULT true
canal_id        TEXT NOT NULL
config_json     JSONB
dna_json        JSONB
created_at      TIMESTAMPTZ DEFAULT now()
```

---

## Deploy

### Paperclip
```yaml
# docker-compose.yml
services:
  paperclip:
    image: paperclipai/paperclip:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://...
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: paperclip
      POSTGRES_USER: paperclip
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### MCP Server
Roda diretamente no VPS (não em container) para ter acesso ao filesystem local (temp files de yt-dlp, ffmpeg, Whisper).

```bash
cd mcp-server
pip install -r requirements.txt
python main.py
```

---

## Secrets no Paperclip

```
OPENAI_API_KEY
YOUTUBE_API_KEY
GOOGLE_CREDENTIALS_PATH
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
SHOTSTACK_API_KEY
SHOTSTACK_ENV
SUPABASE_URL
SUPABASE_KEY
ANTHROPIC_API_KEY   ← para os agentes Claude Code
```

---

## Ordem de Execução

1. Limpar projeto (apagar arquivos obsoletos)
2. Criar nova estrutura de pastas
3. Escrever `mcp-server/` completo
4. Criar `docker-compose.yml` para Paperclip + PostgreSQL
5. Criar migration Supabase (schema expandido)
6. Subir Paperclip no VPS via Docker
7. Configurar Supabase MCP no Paperclip
8. Criar Company + Agents + Routines no Paperclip
9. Configurar secrets
10. Smoke test pipeline ponta a ponta
