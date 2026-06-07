# YT DARK v2

Sistema autônomo de mineração, análise e produção de vídeos para YouTube.
Orquestrado pelo **Paperclip** com agentes Claude Code executando o pipeline completo.

## Arquitetura

```
VPS
├── Paperclip (Docker, porta 3100)   orquestrador + dashboard
│   └── Agentes Claude Code          pipeline autônomo
└── mcp-server (Python, stdio)       yt-dlp + ffmpeg + Whisper

Cloud
└── Supabase                         persistência de dados
```

## Pipeline

| Fase | Trigger | Agente | Gate |
|------|---------|--------|------|
| Descoberta de canais | Routine seg 9h | Descoberta | — |
| Mineração de vídeos | Routine diária 8h | Minerador | ⏸️ você aprova candidatos |
| Análise visual | Vídeo aprovado | Analisador | — |
| Produção | Análise pronta | Produtor | ⏸️ você revisa vídeo final |
| Publicação | Vídeo aprovado | Publicador | — |

## Setup VPS

### 1. Instalar Paperclip (Docker)

```bash
git clone https://github.com/paperclipai/paperclip.git ~/paperclip
cd ~/paperclip
cp docker/.env.example docker/.env

# Edite docker/.env:
# BETTER_AUTH_SECRET=<openssl rand -base64 32>
# PAPERCLIP_PUBLIC_URL=http://SEU_IP:3100

docker compose -f docker/docker-compose.yml up -d
```

Acesse `http://SEU_IP:3100` e crie sua conta admin.

### 2. Instalar MCP Server

```bash
# Dependências de sistema
sudo apt install -y ffmpeg
pip install yt-dlp openai-whisper

# Instalar MCP server
cd ~/ytdark/mcp-server
pip install -r requirements.txt
```

O MCP server roda via stdio — o Paperclip conecta automaticamente ao configurar o agente.

### 3. Aplicar migrations Supabase

```bash
cd ~/ytdark
supabase link --project-ref SEU_PROJECT_REF
supabase db push
```

## Configuração no Paperclip

Após subir o Paperclip (`http://VPS:3100`):

1. Criar **Company**: `mofmoney`
2. Definir **Goal**: "Publicar 4 vídeos/semana sobre finanças pessoais em inglês"
3. Configurar **MCP ytdark-tools**: `python ~/ytdark/mcp-server/main.py` (stdio)
4. Configurar **MCP Supabase** (oficial)
5. Adicionar **secrets** (ver abaixo)
6. Criar **5 agentes** com routines

## Secrets

Configure em Paperclip → Settings → Secrets:

```
ANTHROPIC_API_KEY      agentes Claude Code
OPENAI_API_KEY         GPT-4o + DALL-E 3
YOUTUBE_API_KEY        descoberta + mineração + publicação
ELEVENLABS_API_KEY     narração
ELEVENLABS_VOICE_ID    voz clonada
SHOTSTACK_API_KEY      renderização de vídeo
SUPABASE_URL           banco de dados
SUPABASE_KEY           banco de dados (service_role)
GOOGLE_CREDENTIALS_PATH  Google Drive
```

## Estrutura do Projeto

```
YT DARK/
├── mcp-server/
│   ├── main.py              entry point MCP (stdio)
│   ├── tools/
│   │   ├── downloader.py    yt-dlp wrapper
│   │   ├── transcriber.py   Whisper wrapper
│   │   └── frames.py        ffmpeg wrapper
│   └── requirements.txt
├── canais/
│   └── mofmoney/
│       ├── config.json      filtros de mineração
│       └── channel_dna.json identidade do canal
├── supabase/
│   └── migrations/          schema do banco
├── templates/               Shotstack (whiteboard, talking_head)
└── docs/
    └── superpowers/
        ├── specs/           design docs
        └── plans/           planos de implementação
```

## Custo estimado por vídeo

| Serviço | Custo |
|---------|-------|
| GPT-4o Vision (análise) | ~$0.03 |
| GPT-4o texto (roteiro) | ~$0.02 |
| DALL-E 3 (thumbnail) | ~$0.04 |
| ElevenLabs (narração) | ~$0.15 |
| Shotstack (vídeo) | ~$0.50–$1.00 |
| **Total** | **~$0.75–$1.25** |
