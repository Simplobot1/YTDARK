# YT DARK — Sistema de Mineração, Análise e Produção de Vídeos

**Data:** 2026-05-24
**Revisado:** 2026-05-24 (v2 — decisões finais)
**Canal principal:** [@mofmoney](https://www.youtube.com/@mofmoney)
**Canais fonte iniciais:** @CasuallyFinance, @nickinvestsUS
**Nicho:** Finanças pessoais em inglês

---

## 1. Visão Geral

Sistema **manual e multi-canal** que:

1. **Descobre** canais do YouTube por métricas de performance (não keywords)
2. **Minera** vídeos de alta performance no nicho de finanças
3. **Analisa** estrutura visual e roteiro de cada vídeo com IA
4. **Produz** vídeos **originais** no DNA do canal — remodelando tema e formato, nunca copiando
5. **Armazena** arquivos no Google Drive e metadados no Google Sheets
6. **Publica** no YouTube com título, thumbnail e tags otimizados

**Operação:** 100% manual — cada fase é disparada via Swagger UI pelo operador, por canal. Sem automação automática. Sem scheduler.

**Multi-canal:** cada canal é independente — config, Sheets, Drive e DNA próprios. Adicionar novo canal = criar nova pasta em `canais/`.

---

## 2. Princípio de Conteúdo Original

O sistema **remodela**, não copia.

| O que o sistema FAZ | O que o sistema NÃO FAZ |
|---|---|
| Analisa a estrutura do vídeo (intro, pontos, CTA) | Copia roteiro palavra por palavra |
| Identifica formato visual (whiteboard, talking head) | Reutiliza áudio ou imagens do original |
| Extrai tema e ângulo que performaram bem | Baixa o vídeo final para reusar |
| Usa análise como briefing para o GPT-4o | Copia thumbnail do vídeo fonte |
| Gera thumbnail original com DALL-E 3 | — |

O GPT-4o recebe: tema + ângulo + transcrição (para entender argumento) + DNA do canal.
Output: roteiro completamente novo, na voz e estilo do canal.

---

## 3. Arquitetura

```
FastAPI (backend central — VPS, só compute, sem armazenamento permanente)
├── Swagger UI               → operação manual por canal e fase
├── yt-dlp + ffmpeg          → scraping e extração de frames (temp no VPS)
├── OpenAI Whisper (local)   → transcrição gratuita dos vídeos fonte
├── Browser-use + VidIQ      → keyword research por nicho (gratuito)
├── YouTube Data API v3      → descoberta de canais + mineração + upload
├── GPT-4o Vision            → análise de estrutura visual dos frames
├── GPT-4o texto             → geração de roteiro original
├── DALL-E 3                 → geração de thumbnail original
├── ElevenLabs               → narração em voz clonada
├── Shotstack API            → montagem e renderização do vídeo na nuvem
├── Google Drive API         → armazenamento permanente
├── Google Sheets API        → banco de dados / painel por canal
└── YouTube Data API v3      → upload e publicação final
```

**VPS:** compute only — arquivos temporários apagados após upload pro Drive.
**Sem scheduler:** todas as operações são disparadas manualmente.

---

## 4. Channel DNA

Cada canal tem uma identidade imutável que garante consistência visual e editorial.

```
canais/{id}/
├── config.json         ← filtros operacionais e configurações técnicas
└── channel_dna.json    ← identidade permanente do canal
```

### channel_dna.json

```json
{
  "estilo_visual": "whiteboard",
  "tom_voz": "casual and educational",
  "paleta_cores": ["#FF6B35", "#FFFFFF", "#2C3E50"],
  "estrutura_roteiro": {
    "intro_max_sec": 30,
    "hook_style": "bold question or shocking stat",
    "num_pontos": 5,
    "cta_style": "subscribe + next video suggestion"
  },
  "thumbnail": {
    "formula": "bold text left + visual right",
    "fonte": "Montserrat Bold",
    "cores_principais": ["#FF6B35", "#FFFFFF"]
  },
  "titulo_formula": "[Number] Ways to [Benefit] (No [Common Excuse])",
  "duracao_alvo_min": 12
}
```

**Ciclo de evolução do DNA:**
- Fase 1 (início): operador define DNA baseado nos canais referência
- Fase 2 (após 3–4 vídeos): YouTube Analytics informa CTR e watch time → DNA refinado com dados reais
- Fase 3 (consolidado): DNA travado, todos os vídeos produzidos dentro desse formato

---

## 5. Arquitetura de Serviços (Swappável)

Cada ferramenta fica encapsulada em seu próprio service. Trocar ferramenta = mexer em um único arquivo.

| Service | Hoje | Pode trocar por |
|---|---|---|
| `narrador.py` | ElevenLabs | PlayHT, Murf, voz local |
| `editor.py` | Shotstack | Remotion, MoviePy |
| `analisador.py` | GPT-4o Vision | Claude, Gemini |
| `roteirista.py` | GPT-4o texto | Claude, Llama local |
| `thumbnail.py` | DALL-E 3 | Midjourney, Ideogram |
| `vidiq_scraper.py` | Browser-use | API futura se lançarem |
| `db.py` | Google Sheets | Supabase (quando escalar) |
| `transcritor.py` | Whisper local | AssemblyAI, Deepgram |

**Migration path para Supabase:** a camada `db.py` abstrai todas as operações de dados. Trocar para Supabase = nova implementação de `db.py`, zero mudança no restante da aplicação.

---

## 6. Estrutura de Pastas

### Projeto local / VPS

```
YT DARK/
├── app/
│   ├── main.py                      ← FastAPI app
│   ├── routes/
│   │   ├── descoberta.py            ← descoberta de canais por métricas
│   │   ├── mineracao.py             ← mineração de vídeos
│   │   ├── analise.py               ← análise de estrutura visual
│   │   ├── producao.py              ← geração de roteiro + áudio + vídeo
│   │   └── publicacao.py            ← publicação no YouTube
│   ├── services/
│   │   ├── channel_discovery.py     ← descoberta por métricas (seed + categoria)
│   │   ├── scraper.py               ← yt-dlp wrapper
│   │   ├── transcritor.py           ← Whisper local
│   │   ├── vidiq_scraper.py         ← browser-use + VidIQ
│   │   ├── analisador.py            ← GPT-4o Vision
│   │   ├── roteirista.py            ← GPT-4o texto + DNA
│   │   ├── thumbnail.py             ← DALL-E 3
│   │   ├── narrador.py              ← ElevenLabs
│   │   ├── editor.py                ← Shotstack
│   │   ├── drive.py                 ← Google Drive upload/download
│   │   ├── db.py                    ← abstração de dados (Sheets hoje, Supabase depois)
│   │   └── publicador.py            ← YouTube API
│   └── models/
│       ├── video.py
│       ├── canal.py
│       └── canal_candidato.py
├── canais/
│   └── mofmoney/
│       ├── config.json
│       └── channel_dna.json
├── docs/
│   └── superpowers/specs/
├── templates/
│   ├── whiteboard/
│   │   ├── shotstack.json
│   │   └── prompt_roteiro.txt
│   ├── talking_head/
│   │   ├── shotstack.json
│   │   └── prompt_roteiro.txt
│   └── slides/
│       ├── shotstack.json
│       └── prompt_roteiro.txt
├── temp/                            ← apagado após upload
├── credentials/
│   ├── google_credentials.json
│   └── .env
└── requirements.txt
```

### Google Drive

```
Drive/
└── YT DARK/
    └── mofmoney/
        ├── frames/
        ├── thumbnails/
        ├── roteiros/
        ├── audio/
        └── producao/
```

### Google Sheets (por canal)

**Aba: Pipeline**
| video_id | título | canal_fonte | views | data_pub | tipo | score | status | drive_link | yt_link |
|---|---|---|---|---|---|---|---|---|---|

Status: `candidato → aprovado → minerado → analisado → roteiro_gerado → audio_gerado → video_pronto → publicado`

**Aba: Canais Fonte** (editável manualmente)
| handle | nome | ativo | min_views | max_dias | última_mineração |
|---|---|---|---|---|---|

**Aba: Canais Candidatos** (resultado da descoberta)
| handle | subscribers | avg_views | engagement_rate | upload_freq | score | adicionado |
|---|---|---|---|---|---|---|

**Aba: Keywords** (resultado VidIQ)
| termo | volume | competition | seo_score | data |
|---|---|---|---|---|

**Aba: Análises** — estrutura visual detalhada por vídeo
**Aba: Publicados** — histórico completo

---

## 7. Módulo de Descoberta de Canais (Fase 0)

### Objetivo
Encontrar canais candidatos para usar como fonte, baseado em métricas de performance — não keywords.

### Duas estratégias

**Seed Discovery:** parte de um canal conhecido → encontra canais relacionados/similares → filtra por métricas

**Category Discovery:** parte de um nicho amplo → busca canais no YouTube → filtra por métricas

### Métricas calculadas por canal candidato

| Métrica | Cálculo | Peso no Score |
|---|---|---|
| `avg_views` | Média dos últimos 20 vídeos | 40% |
| `engagement_rate` | (likes + comments) / views | 30% |
| `upload_freq` | Vídeos por mês | 20% |
| `momentum` | Views últimos 30d vs histórico | 10% |
| `avg_duration` | Duração média em minutos | Filtro (não score) |
| `subscribers` | Faixa configurável | Filtro (não score) |

### Endpoint

```
POST /descobrir-canais
{
  "estrategia": "seed" | "categoria",
  "seed_channel": "@CasuallyFinance",
  "nicho": "personal finance",
  "idioma": "en",
  "filtros": {
    "subscribers_min": 100000,
    "subscribers_max": 3000000,
    "avg_views_min": 50000,
    "upload_freq_min": 4,
    "avg_duration_min_min": 8,
    "avg_duration_max_min": 20
  },
  "top_n": 20
}
```

### Fontes de dados
- YouTube Data API v3 `search.list` (type=channel) — candidatos iniciais
- YouTube Data API v3 `channels.list` — subscribers, stats gerais
- YouTube Data API v3 `videos.list` (últimos 20 vídeos) — avg_views, engagement, duração
- yt-dlp `--dump-json` — canais relacionados/featured (para seed discovery)

---

## 8. Módulo de Pesquisa VidIQ (Fase 0.5)

### Objetivo
Extrair keywords do nicho com volume de busca, dificuldade e SEO score para enriquecer a seleção de vídeos.

### Implementação
```python
# services/vidiq_scraper.py
from browser_use import Agent
from langchain_openai import ChatOpenAI

async def buscar_keywords_vidiq(nicho: str, idioma: str = "en"):
    agent = Agent(
        task=f"Acesse vidiq.com, vá em Keyword Research, busque '{nicho}'. "
             f"Extraia top 20 keywords com: termo, volume, competition score, SEO score. "
             f"Retorne como lista JSON.",
        llm=ChatOpenAI(model="gpt-4o")
    )
    return await agent.run()
```

Resultado salvo na aba "Keywords" do Sheets do canal.

---

## 9. Pipeline Completo

### Fase 0 — Descoberta de Canais Fonte (manual, uma vez por nicho)
```
POST /descobrir-canais → lista ranqueada de candidatos
Operador seleciona quais adicionar → salva em aba "Canais Fonte" do Sheets
```

### Fase 0.5 — Keyword Research (manual, periódico)
```
POST /canais/{canal}/keywords → browser-use no VidIQ
Resultado salvo na aba "Keywords" do Sheets
```

### Fase 1 — Mineração (manual, por canal)
```
YouTube Data API → busca vídeos dos canais fonte
Filtra: views, data, duração, sem PT
Score: avg_views_ratio (40%) + engagement (30%) + keyword_fit (20%) + dna_fit (10%)
yt-dlp → metadados + thumbnail
Whisper → transcrição local
Salva no Sheets (status: candidato) com score calculado
Operador aprova quais seguir → status: aprovado
```

### Fase 2 — Análise de Estrutura (manual, por vídeo aprovado)
```
yt-dlp → frames-chave (temp VPS)
GPT-4o Vision → analisa:
  - tipo de vídeo
  - elementos visuais (textos, ícones, cores)
  - estrutura do roteiro (intro, pontos, CTA)
  - estilo da thumbnail
Frames → Drive /frames/
Análise → Sheets (status: analisado)
Temp apagado
```

### Fase 3 — Produção (manual, por vídeo analisado)
```
Análise + transcrição + channel_dna.json → GPT-4o
  → Roteiro ORIGINAL no DNA do canal
Roteiro → Drive /roteiros/ + Sheets

ElevenLabs → narração .mp3
.mp3 → Drive /audio/

DALL-E 3 + channel_dna.json → thumbnail original
Thumbnail → Drive /thumbnails/

Shotstack → monta vídeo com template do tipo detectado
  Usa template DNA do canal (cores, fonte, animações)
  Renderiza na nuvem → .mp4
.mp4 → Drive /producao/
Sheets (status: video_pronto + drive_link)
```

### Fase 4 — Publicação (manual, com aprovação)
```
Operador revisa .mp4 no Drive
Confirma publicação no Swagger
.mp4 do Drive → YouTube Data API v3
  - Título gerado por GPT-4o (formula do DNA)
  - Descrição e tags
  - Thumbnail do Drive
  - Categoria e idioma
Sheets (status: publicado + yt_link)
```

---

## 10. Config por Canal

### config.json
```json
{
  "canal_id": "mofmoney",
  "youtube_handle": "@mofmoney",
  "idioma": "en",
  "nicho_keywords": ["personal finance", "investing", "passive income"],
  "canais_fonte": ["@CasuallyFinance", "@nickinvestsUS"],
  "tipo_video_padrao": "whiteboard",
  "tipos_video_suportados": ["whiteboard", "talking_head"],
  "elevenlabs_voice_id": "",
  "google_sheets_id": "",
  "google_drive_folder_id": "",
  "filtros_mineracao": {
    "min_views": 50000,
    "max_dias": 30,
    "duracao_min_min": 8,
    "duracao_max_min": 20,
    "sem_legenda_pt": true
  }
}
```

---

## 11. API Endpoints (FastAPI)

```
# Descoberta
POST /descobrir-canais                            → descobre canais por métricas
POST /canais/{canal}/keywords                     → keyword research via VidIQ

# Mineração
POST /canais/{canal}/minerar                      → minera e pontua candidatos
GET  /canais/{canal}/candidatos                   → lista candidatos com score
POST /canais/{canal}/aprovar/{video_id}           → aprova candidato para produção

# Análise
POST /canais/{canal}/analisar/{video_id}          → analisa estrutura visual
GET  /canais/{canal}/analisados                   → lista análises prontas

# Produção
POST /canais/{canal}/produzir/{video_id}          → gera roteiro + áudio + vídeo
GET  /canais/{canal}/fila                         → status da fila

# Publicação
POST /canais/{canal}/publicar/{video_id}          → publica no YouTube
GET  /canais/{canal}/publicados                   → histórico

# Configuração
GET  /canais                                      → lista todos os canais
GET  /canais/{canal}/config                       → configuração + DNA do canal
PUT  /canais/{canal}/config                       → atualiza configuração
PUT  /canais/{canal}/dna                          → atualiza channel DNA
```

Acesso via **Swagger UI** em `http://localhost:8000/docs`.

---

## 12. Templates de Vídeo

| Tipo | Estilo visual | Referência |
|---|---|---|
| `whiteboard` | Fundo branco, animações, narração | @nickinvestsUS |
| `talking_head` | Apresentador + lower thirds + gráficos | @CasuallyFinance |
| `slides` | Slides coloridos + bullet points | genérico |

Cada template tem: `shotstack.json` (montagem) + `prompt_roteiro.txt` (instrução GPT-4o para esse estilo).

Adicionar novo estilo = criar pasta em `templates/` com esses dois arquivos.

---

## 13. Stack Completo

| Camada | Ferramenta | Custo estimado |
|---|---|---|
| Backend | FastAPI | Grátis |
| Scraping | yt-dlp + ffmpeg | Grátis |
| Transcrição | OpenAI Whisper (local) | Grátis |
| Keyword research | Browser-use + VidIQ | Grátis |
| Descoberta de canais | YouTube Data API v3 | Grátis |
| IA — análise visual | GPT-4o Vision | ~$0.03/vídeo |
| IA — roteiro | GPT-4o texto | ~$0.02/vídeo |
| IA — thumbnail | DALL-E 3 | ~$0.04/vídeo |
| Narração | ElevenLabs | ~$0.15/vídeo ($5/mês) |
| Montagem de vídeo | Shotstack | ~$0.50–$1.00/vídeo |
| Armazenamento | Google Drive | Grátis 15GB / $3/mês 100GB |
| Banco de dados | Google Sheets | Grátis |
| Upload YouTube | YouTube Data API v3 | Grátis |
| Deploy | VPS existente | $0 adicional |
| **Total por vídeo** | | **~$0.75–$1.25** |

---

## 14. Path de Escalabilidade

**Quando tiver 3+ canais ativos ou precisar de queries complexas:**

```python
# Troca transparente — só esse arquivo muda:
# services/db.py

# Hoje:
from services.sheets_impl import SheetsDatabase as Database

# Ao escalar:
from services.supabase_impl import SupabaseDatabase as Database
```

O restante da aplicação não muda. Supabase já está no `.env` pronto para quando chegar a hora.

---

## 15. Credenciais Necessárias

### Google Cloud
- [ ] Ativar: YouTube Data API v3, Google Drive API, Google Sheets API
- [ ] Criar credenciais OAuth 2.0 → baixar `credentials/google_credentials.json`
- [ ] Autorizar com a conta do canal @mofmoney

### OpenAI
- [ ] `OPENAI_API_KEY` — GPT-4o + DALL-E 3 + Whisper API (se usar cloud)

### ElevenLabs
- [ ] `ELEVENLABS_API_KEY`
- [ ] `ELEVENLABS_VOICE_ID`

### Shotstack
- [ ] `SHOTSTACK_API_KEY`

### Google Sheets + Drive
- [ ] Criar planilha para @mofmoney → ID no config.json
- [ ] Criar pasta YT DARK/mofmoney no Drive → ID no config.json

---

## 16. Arquivo .env

```env
# OpenAI (GPT-4o + DALL-E 3 + Whisper cloud opcional)
OPENAI_API_KEY=

# ElevenLabs
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Shotstack
SHOTSTACK_API_KEY=
SHOTSTACK_ENV=v1

# Google
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json

# YouTube Data API (para mineração — pode ser API key simples)
YOUTUBE_API_KEY=
```

---

## 17. Ordem de Implementação

1. Setup FastAPI base + estrutura de pastas + .env + requirements.txt
2. Modelos de dados (Video, Canal, CanalCandidato)
3. Camada db.py + implementação Google Sheets
4. Integração Google Drive (upload/download)
5. **Módulo de descoberta de canais** (channel_discovery.py + endpoint)
6. Serviço de scraping (yt-dlp wrapper + yt-dlp featured channels)
7. Serviço de transcrição (Whisper local)
8. Keyword research (browser-use + VidIQ)
9. Endpoint de mineração + score + salva no Sheets
10. Serviço de análise GPT-4o Vision + salva no Drive/Sheets
11. Serviço de geração de roteiro GPT-4o + channel_dna.json
12. Geração de thumbnail com DALL-E 3
13. Integração ElevenLabs (narração) + salva no Drive
14. Template whiteboard no Shotstack + salva .mp4 no Drive
15. Endpoint de publicação YouTube API
16. Deploy no VPS + setup git + GitHub Actions (CI básico)

---

## 18. Expansão para Novos Canais

1. Criar pasta `canais/{novo_canal}/`
2. Criar `config.json` e `channel_dna.json`
3. Criar planilha Google Sheets → ID no config
4. Criar pasta no Drive → ID no config
5. Rodar `/descobrir-canais` com seed ou categoria do nicho
6. Sistema está pronto para operar esse canal de forma independente
