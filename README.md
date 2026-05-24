# YT DARK

Sistema de mineração, análise e produção de vídeos para YouTube.

## Setup Backend

```bash
pip install -r requirements.txt
cp .env.example .env
# Preencha as keys no .env
uvicorn app.main:app --reload
```

Acesse http://localhost:8000/docs para o Swagger UI.

## Fluxo de Uso

1. `POST /descobrir-canais` — encontra canais por métricas do YouTube
2. `POST /canais/{id}/keywords` — pesquisa keywords via VidIQ
3. `POST /canais/{id}/minerar` — minera vídeos com score ponderado
4. `POST /canais/{id}/aprovar/{video_id}` — aprova candidato para produção
5. `POST /canais/{id}/analisar/{video_id}` — analisa estrutura visual (GPT-4o Vision)
6. `POST /canais/{id}/produzir/{video_id}` — gera roteiro + thumbnail + áudio + vídeo
7. `POST /canais/{id}/publicar/{video_id}` — publica no YouTube (private, manual review)

## Canais

Cada canal configurado em `canais/{id}/`:
- `config.json` — filtros de mineração, canais fonte, configurações
- `channel_dna.json` — identidade visual, tom de voz, fórmulas de título e thumbnail

## Variáveis de Ambiente (.env)

```
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
SHOTSTACK_API_KEY=...
SHOTSTACK_ENV=v1
JWT_SECRET=change-me-in-production
USERS=admin@email.com:senha123
```

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edite NEXT_PUBLIC_API_URL com a URL do backend
npm run dev
```

Acesse http://localhost:3000

## Deploy

- **Backend**: VPS com Python 3.11+. Deploy via `git pull && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Frontend**: Cloudflare Pages (auto-deploy via GitHub Actions ao fazer push em `main`)
