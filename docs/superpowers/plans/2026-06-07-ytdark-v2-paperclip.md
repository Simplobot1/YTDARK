# YT DARK v2 — Paperclip + MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reconstruir YT DARK sobre Paperclip como orquestrador central, com MCP server para ferramentas pesadas e agentes Claude Code executando o pipeline autônomo.

**Architecture:** Paperclip roda em Docker no VPS (PostgreSQL embutido). Um MCP server Python expõe yt-dlp, ffmpeg e Whisper como tools. Supabase Cloud persiste todos os dados. Agentes Claude Code no Paperclip executam cada fase do pipeline.

**Tech Stack:** Paperclip (Node.js, Docker), Python MCP (`mcp` SDK), yt-dlp, ffmpeg, Whisper, Supabase, YouTube Data API, OpenAI, ElevenLabs, Shotstack.

---

## O que roda onde

```
VPS
├── Paperclip (Docker container) — porta 3100
├── mcp-server (Python, processo direto) — stdio
└── Repo YT DARK clonado (mcp-server/ + canais/ + templates/)

Cloud
└── Supabase (já existe)
```

---

## File Map

**Criar:**
- `mcp-server/main.py` — entry point MCP server
- `mcp-server/tools/__init__.py`
- `mcp-server/tools/downloader.py` — yt-dlp wrapper
- `mcp-server/tools/transcriber.py` — Whisper wrapper
- `mcp-server/tools/frames.py` — ffmpeg wrapper
- `mcp-server/requirements.txt`
- `mcp-server/README.md`
- `supabase/migrations/20260607_001_v2_schema.sql` — canais table + aprovado

**Deletar:**
- `app/` — FastAPI inteiro
- `frontend/` — Next.js
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `pytest.ini`
- `check_canal.py`, `check_logs.py`, `check_ssl.py`, `check_ssl2.py`
- `check_traefik.py`, `check_traefik2.py`, `check_traefik3.py`
- `check_vps.py`, `deploy.py`, `deploy_now.py`, `deploy_swarm.py`
- `fix_credentials.py`, `force_restart.py`, `push_backend.py`
- `redeploy_stack.py`, `setup_vps.py`, `test_login.py`
- `temp/` (se existir)

**Manter intacto:**
- `canais/`
- `credentials/`
- `supabase/migrations/` (existentes)
- `templates/`
- `docs/`
- `AGENTS.md`

---

## Task 1: Limpar projeto

**Files:** Deletar tudo obsoleto

- [ ] **Step 1: Deletar app/**
```bash
rm -rf "C:/Users/ricar/projetos/YT DARK/app"
```

- [ ] **Step 2: Deletar frontend/**
```bash
rm -rf "C:/Users/ricar/projetos/YT DARK/frontend"
```

- [ ] **Step 3: Deletar scripts avulsos na raiz**
```bash
cd "C:/Users/ricar/projetos/YT DARK"
rm -f Dockerfile docker-compose.yml requirements.txt pytest.ini
rm -f check_canal.py check_logs.py check_ssl.py check_ssl2.py
rm -f check_traefik.py check_traefik2.py check_traefik3.py check_vps.py
rm -f deploy.py deploy_now.py deploy_swarm.py
rm -f fix_credentials.py force_restart.py push_backend.py
rm -f redeploy_stack.py setup_vps.py test_login.py
rm -rf temp
```

- [ ] **Step 4: Verificar o que sobrou**
```bash
ls "C:/Users/ricar/projetos/YT DARK"
```
Expected: `canais/  credentials/  docs/  supabase/  templates/  AGENTS.md  README.md`

- [ ] **Step 5: Commit**
```bash
cd "C:/Users/ricar/projetos/YT DARK"
git add -A
git commit -m "chore: remove FastAPI backend e frontend (v2 Paperclip)"
```

---

## Task 2: Criar estrutura mcp-server

**Files:**
- Create: `mcp-server/tools/__init__.py`
- Create: `mcp-server/requirements.txt`

- [ ] **Step 1: Criar diretório**
```bash
mkdir -p "C:/Users/ricar/projetos/YT DARK/mcp-server/tools"
```

- [ ] **Step 2: Criar requirements.txt**
```
mcp>=1.0.0
yt-dlp>=2024.1.0
openai-whisper>=20231117
```

- [ ] **Step 3: Criar __init__.py vazio**
```python
# tools/__init__.py
```

- [ ] **Step 4: Verificar**
```bash
ls "C:/Users/ricar/projetos/YT DARK/mcp-server"
ls "C:/Users/ricar/projetos/YT DARK/mcp-server/tools"
```
Expected: `requirements.txt  tools/` e dentro de tools: `__init__.py`

---

## Task 3: Tool — downloader.py

**Files:**
- Create: `mcp-server/tools/downloader.py`

- [ ] **Step 1: Escrever downloader.py**

```python
import subprocess
import json
import os


def download_video(url: str, output_dir: str = "/tmp/ytdark") -> dict:
    """Baixa vídeo e retorna metadados + caminho local."""
    os.makedirs(output_dir, exist_ok=True)

    meta_result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True, text=True, timeout=60
    )
    if meta_result.returncode != 0:
        raise RuntimeError(f"yt-dlp metadata falhou: {meta_result.stderr}")

    meta = json.loads(meta_result.stdout)
    video_id = meta["id"]
    ext = meta.get("ext", "mp4")
    output_path = os.path.join(output_dir, f"{video_id}.{ext}")

    dl_result = subprocess.run(
        ["yt-dlp", "--no-playlist", "-o", output_path, url],
        capture_output=True, text=True, timeout=600
    )
    if dl_result.returncode != 0:
        raise RuntimeError(f"yt-dlp download falhou: {dl_result.stderr}")

    return {
        "video_id": video_id,
        "title": meta.get("title", ""),
        "duration": meta.get("duration", 0),
        "channel": meta.get("channel", ""),
        "view_count": meta.get("view_count", 0),
        "path": output_path,
    }


def get_channel_related(handle: str) -> list[dict]:
    """Busca canais relacionados/featured de um canal via yt-dlp."""
    url = f"https://www.youtube.com/{handle}"
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--flat-playlist", "--no-warnings", url],
        capture_output=True, text=True, timeout=60
    )
    channels = []
    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
            if data.get("_type") == "url" and "channel" in data.get("url", ""):
                channels.append({
                    "url": data["url"],
                    "title": data.get("title", ""),
                })
        except json.JSONDecodeError:
            continue
    return channels
```

---

## Task 4: Tool — transcriber.py

**Files:**
- Create: `mcp-server/tools/transcriber.py`

- [ ] **Step 1: Escrever transcriber.py**

```python
import subprocess
import os


def transcribe(video_path: str, language: str = "en") -> str:
    """Transcreve vídeo/áudio usando Whisper local. Retorna texto."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    output_dir = os.path.dirname(video_path)

    result = subprocess.run(
        [
            "whisper", video_path,
            "--language", language,
            "--output_format", "txt",
            "--output_dir", output_dir,
            "--model", "base",
        ],
        capture_output=True, text=True, timeout=1800
    )

    if result.returncode != 0:
        raise RuntimeError(f"Whisper falhou: {result.stderr}")

    base = os.path.splitext(video_path)[0]
    txt_path = base + ".txt"

    if not os.path.exists(txt_path):
        raise RuntimeError(f"Arquivo de transcrição não encontrado: {txt_path}")

    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read().strip()
```

---

## Task 5: Tool — frames.py

**Files:**
- Create: `mcp-server/tools/frames.py`

- [ ] **Step 1: Escrever frames.py**

```python
import subprocess
import json
import os


def extract_frames(video_path: str, n_frames: int = 10) -> list[str]:
    """Extrai n_frames distribuídos uniformemente do vídeo. Retorna lista de caminhos."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    base = os.path.splitext(video_path)[0]
    output_dir = base + "_frames"
    os.makedirs(output_dir, exist_ok=True)

    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            video_path,
        ],
        capture_output=True, text=True, timeout=30
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {probe.stderr}")

    info = json.loads(probe.stdout)
    duration = float(info["format"]["duration"])

    frame_paths = []
    for i in range(n_frames):
        timestamp = (duration / n_frames) * i
        output_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
        subprocess.run(
            [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                output_path, "-y",
            ],
            capture_output=True, timeout=30
        )
        if os.path.exists(output_path):
            frame_paths.append(output_path)

    return frame_paths
```

---

## Task 6: MCP Server — main.py

**Files:**
- Create: `mcp-server/main.py`

- [ ] **Step 1: Escrever main.py**

```python
import asyncio
import json
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.downloader import download_video, get_channel_related
from tools.transcriber import transcribe
from tools.frames import extract_frames

server = Server("ytdark-tools")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="download_video",
            description="Baixa um vídeo do YouTube com yt-dlp e retorna metadados e caminho local.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL do vídeo YouTube"},
                    "output_dir": {
                        "type": "string",
                        "description": "Diretório de saída (default: /tmp/ytdark)",
                        "default": "/tmp/ytdark",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_channel_related",
            description="Retorna canais relacionados/featured de um canal YouTube via yt-dlp.",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Handle do canal (ex: @CasuallyFinance)",
                    }
                },
                "required": ["handle"],
            },
        ),
        Tool(
            name="extract_frames",
            description="Extrai N frames distribuídos de um vídeo com ffmpeg. Retorna lista de caminhos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Caminho local do vídeo"},
                    "n_frames": {
                        "type": "integer",
                        "description": "Número de frames a extrair (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["video_path"],
            },
        ),
        Tool(
            name="transcribe",
            description="Transcreve áudio de um vídeo usando Whisper local. Retorna texto completo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Caminho local do vídeo"},
                    "language": {
                        "type": "string",
                        "description": "Idioma do áudio (default: en)",
                        "default": "en",
                    },
                },
                "required": ["video_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "download_video":
            result = download_video(
                arguments["url"],
                arguments.get("output_dir", "/tmp/ytdark"),
            )
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_channel_related":
            result = get_channel_related(arguments["handle"])
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "extract_frames":
            paths = extract_frames(
                arguments["video_path"],
                arguments.get("n_frames", 10),
            )
            return [TextContent(type="text", text=json.dumps({"frames": paths}))]

        elif name == "transcribe":
            text = transcribe(
                arguments["video_path"],
                arguments.get("language", "en"),
            )
            return [TextContent(type="text", text=json.dumps({"transcript": text}))]

        else:
            raise ValueError(f"Tool desconhecida: {name}")

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Commit MCP server**
```bash
cd "C:/Users/ricar/projetos/YT DARK"
git add mcp-server/
git commit -m "feat: ytdark-tools MCP server (yt-dlp + ffmpeg + Whisper)"
```

---

## Task 7: Supabase migration — canais table

**Files:**
- Create: `supabase/migrations/20260607_001_v2_schema.sql`

- [ ] **Step 1: Escrever migration**

```sql
-- YT DARK v2 — adiciona tabela canais e coluna aprovado

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

-- Seed: inserir canal mofmoney
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
```

- [ ] **Step 2: Commit migration**
```bash
cd "C:/Users/ricar/projetos/YT DARK"
git add supabase/migrations/20260607_001_v2_schema.sql
git commit -m "feat: supabase migration v2 — tabela canais + aprovado"
```

---

## Task 8: Atualizar README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Reescrever README**

```markdown
# YT DARK v2

Sistema autônomo de mineração, análise e produção de vídeos para YouTube.
Orquestrado pelo Paperclip com agentes Claude Code.

## Arquitetura

```
Paperclip (Docker, VPS:3100)  — orquestrador + dashboard
├── Agentes Claude Code       — pipeline autônomo
MCP Server (Python, VPS)      — yt-dlp + ffmpeg + Whisper
Supabase (Cloud)              — persistência de dados
```

## Setup VPS

### 1. Instalar Paperclip

```bash
git clone https://github.com/paperclipai/paperclip.git
cd paperclip
cp docker/.env.example docker/.env
# Edite docker/.env com BETTER_AUTH_SECRET e PAPERCLIP_PUBLIC_URL
docker compose -f docker/docker-compose.yml up -d
```

Acesse http://VPS_IP:3100

### 2. Instalar MCP Server

```bash
# No diretório do projeto
cd mcp-server
pip install -r requirements.txt
# Instalar dependências de sistema:
# apt install ffmpeg
# pip install openai-whisper
# pip install yt-dlp
python main.py  # roda via stdio — Paperclip conecta automaticamente
```

### 3. Aplicar migrations Supabase

```bash
supabase link --project-ref SEU_PROJECT_REF
supabase db push
```

## Secrets no Paperclip

Configure em Settings → Secrets:

```
ANTHROPIC_API_KEY
OPENAI_API_KEY
YOUTUBE_API_KEY
GOOGLE_CREDENTIALS_PATH
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
SHOTSTACK_API_KEY
SUPABASE_URL
SUPABASE_KEY
```

## Pipeline

1. **Descoberta** (seg 9h) — ranqueia canais candidatos
2. **Mineração** (diária 8h) — minera vídeos com score
3. ⏸️ **Você aprova** quais vídeos produzir
4. **Análise** (automático) — GPT-4o Vision + Whisper
5. **Produção** (automático) — roteiro + thumbnail + áudio + vídeo
6. ⏸️ **Você aprova** antes de publicar
7. **Publicação** (automático) — upload YouTube
```

- [ ] **Step 2: Commit README**
```bash
cd "C:/Users/ricar/projetos/YT DARK"
git add README.md
git commit -m "docs: README v2 — Paperclip architecture"
```

---

## Task 9 — VPS (você executa)

> ⚠️ Esses passos precisam ser executados por você no VPS. Avise quando estiver pronto.

- [ ] **Step 1: Clonar Paperclip no VPS**
```bash
git clone https://github.com/paperclipai/paperclip.git ~/paperclip
cd ~/paperclip
```

- [ ] **Step 2: Configurar .env do Paperclip**
```bash
cp docker/.env.example docker/.env
# Editar com:
# BETTER_AUTH_SECRET=<gere com: openssl rand -base64 32>
# PAPERCLIP_PUBLIC_URL=http://SEU_IP_VPS:3100
```

- [ ] **Step 3: Subir Paperclip via Docker**
```bash
docker compose -f docker/docker-compose.yml up -d
# Verificar: docker ps
# Acessar: http://SEU_IP_VPS:3100
```

- [ ] **Step 4: Clonar YT DARK no VPS**
```bash
git clone https://github.com/SEU_USER/yt-dark.git ~/ytdark
```

- [ ] **Step 5: Instalar dependências MCP**
```bash
sudo apt install -y ffmpeg
pip install openai-whisper yt-dlp
cd ~/ytdark/mcp-server
pip install -r requirements.txt
```

- [ ] **Step 6: Aplicar migrations Supabase**
```bash
cd ~/ytdark
supabase link --project-ref SEU_PROJECT_REF
supabase db push
```

---

## Task 10 — Configurar Paperclip (você faz no dashboard)

> Após subir o Paperclip, configure pelo dashboard em http://VPS:3100

- [ ] Criar conta admin
- [ ] Criar Company: `mofmoney`
- [ ] Definir Goal: "Publicar 4 vídeos/semana sobre finanças pessoais em inglês"
- [ ] Configurar MCP: ytdark-tools (stdio: `python ~/ytdark/mcp-server/main.py`)
- [ ] Configurar MCP: Supabase (oficial)
- [ ] Adicionar secrets (todas as API keys)
- [ ] Criar 5 agentes + routines (detalhes no próximo plano)

---

## Ordem de execução

1. ✅ Task 1 — Limpeza (Claude executa)
2. ✅ Task 2 — Estrutura (Claude executa)
3. ✅ Task 3-6 — MCP server (Claude executa)
4. ✅ Task 7 — Migration (Claude executa)
5. ✅ Task 8 — README (Claude executa)
6. 👤 Task 9 — VPS setup (você executa)
7. 👤 Task 10 — Paperclip config (você executa no dashboard)
