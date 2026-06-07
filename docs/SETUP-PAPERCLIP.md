# Paperclip — Setup Completo YT DARK

## Acesso

- **URL:** http://178.156.134.29:3100
- **Login:** conta criada no primeiro acesso

---

## 1. Criar Company

**Nome:** `mofmoney`  
**Goal (mission):**

```
You are the autonomous production system for the YouTube channel mofmoney.
Your mission is to find underrated personal finance channels in English, mine their best-performing videos, analyze what makes them work visually and narratively, produce similar videos adapted for the mofmoney style, and publish 4 videos per week consistently.
You operate fully autonomously except for two human approval gates: (1) approving video candidates before download and (2) reviewing the final video before publishing.
```

---

## 2. Secrets

Adicionar em **Settings → Secrets**:

| Key | Valor | Onde pegar |
|-----|-------|-----------|
| `ANTHROPIC_API_KEY` | sua chave Claude | console.anthropic.com |
| `OPENAI_API_KEY` | `sk-proj-jiloss...` (ver .env) | platform.openai.com |
| `YOUTUBE_API_KEY` | `AIzaSyAUTYc...` (ver .env) | Google Cloud Console |
| `SUPABASE_URL` | `https://gddywawuzytndrfxhcwk.supabase.co` | Supabase dashboard |
| `SUPABASE_KEY` | service_role key (ver .env) | Supabase → Settings → API |
| `ELEVENLABS_API_KEY` | a definir | elevenlabs.io |
| `ELEVENLABS_VOICE_ID` | a definir | após clonar voz |
| `SHOTSTACK_API_KEY` | a definir | shotstack.io |

---

## 3. MCP Server — ytdark-tools

**Tipo:** stdio  
**Comando:** `/opt/ytdark/mcp-server/venv/bin/python /opt/ytdark/mcp-server/main.py`

**Tools disponíveis:**
- `download_video(url, output_dir)` — baixa vídeo YouTube com yt-dlp
- `get_channel_related(handle)` — descobre canais relacionados
- `extract_frames(video_path, n_frames)` — extrai frames com ffmpeg

> Whisper foi removido por peso (800MB). Transcrição pode ser feita via OpenAI API diretamente pelo agente.

---

## 4. MCP Server — Supabase (oficial)

Usar o MCP oficial do Supabase.  
**Project ref:** `gddywawuzytndrfxhcwk`  
**URL:** `https://gddywawuzytndrfxhcwk.supabase.co`

---

## 5. Agentes — os 5 do pipeline

### Agente 1: Descoberta
**Nome:** `Descoberta`  
**Routine:** Segunda-feira 9h  
**Instrução resumida:**
```
Use get_channel_related to find underrated personal finance YouTube channels in English.
Filter: between 10k–500k subscribers, posting regularly, high engagement.
Save results to Supabase table canais_candidatos.
```

### Agente 2: Minerador
**Nome:** `Minerador`  
**Routine:** Diária 8h  
**Gate:** Aprovação humana dos canais candidatos  
**Instrução resumida:**
```
Query Supabase for approved channels (aprovado = true).
Use YouTube API to find their top videos from the last 90 days (views > 50k).
Save to Supabase table videos. Pause for human approval before downloading.
```

### Agente 3: Analisador
**Nome:** `Analisador`  
**Trigger:** Vídeo aprovado na tabela videos  
**Instrução resumida:**
```
Download approved video using download_video tool.
Extract 20 frames using extract_frames tool.
Send frames to GPT-4o Vision for visual analysis.
Transcribe audio using OpenAI Whisper API.
Analyze hook, narrative structure, pacing, visual style.
Save analysis to Supabase table videos (campos de análise).
```

### Agente 4: Produtor
**Nome:** `Produtor`  
**Trigger:** Análise pronta  
**Instrução resumida:**
```
Read video analysis from Supabase.
Write a script in the mofmoney style (personal finance, English, engaging hook).
Generate thumbnail prompt for DALL-E 3.
Send script to ElevenLabs for narration.
Send to Shotstack for video rendering.
Save video URL to Supabase. Pause for human review.
```

### Agente 5: Publicador
**Nome:** `Publicador`  
**Trigger:** Vídeo aprovado para publicação  
**Instrução resumida:**
```
Read approved video from Supabase.
Upload to YouTube via YouTube Data API v3.
Set title, description, tags, thumbnail.
Update Supabase with published status and YouTube URL.
```

---

## 6. Schema do Banco (Supabase)

**Projeto:** `gddywawuzytndrfxhcwk` (sa-east-1)  
**Migrations aplicadas:**
- `20260525000001_initial_schema.sql` — tabelas base
- `20260525000002_remodelacao_fields.sql` — campos de remodelação
- `20260607000001_v2_schema.sql` — tabela canais + coluna aprovado

**Tabelas:**
- `canais` — canais fonte aprovados
- `canais_candidatos` — descobertos, aguardam aprovação (campo `aprovado`)
- `videos` — vídeos minerados e produzidos

---

## 7. Infra VPS

| Serviço | Status | Porta |
|---------|--------|-------|
| Paperclip | ✅ rodando | 3100 |
| mcp-server | ✅ instalado | stdio |
| Traefik | ✅ | 80/443 |
| n8n | ✅ | — |

**mcp-server path:** `/opt/ytdark/mcp-server/`  
**Paperclip data:** `/opt/paperclip-data/`  
**Paperclip compose:** `/root/paperclip-run.yml`  
**Código YT DARK:** `/opt/ytdark/`

**Reiniciar Paperclip (se necessário):**
```bash
docker compose -f /root/paperclip-run.yml restart
```

---

## 8. GitHub

**Repo:** https://github.com/Simplobot1/YTDARK  
**Branch:** main
