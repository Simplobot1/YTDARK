# YTDARK Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend for YTDARK — descoberta de canais, mineração de vídeos, análise visual, produção de conteúdo original e publicação no YouTube.

**Architecture:** FastAPI com service layer pattern. Cada integração externa (YouTube, OpenAI, ElevenLabs, Shotstack, Google Drive/Sheets) isolada em seu próprio service file. Camada `db.py` abstrai o banco de dados (Google Sheets hoje, Supabase-ready). JWT auth para o frontend.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, yt-dlp, openai (GPT-4o + DALL-E 3), openai-whisper, browser-use, langchain-openai, elevenlabs, google-api-python-client, gspread, python-jose, passlib, pytest, pytest-asyncio, pytest-mock, httpx

---

## File Structure

```
app/
├── main.py                    ← FastAPI app + CORS + routers
├── config.py                  ← pydantic-settings (lê .env)
├── auth.py                    ← JWT encode/decode/verify
├── models/
│   ├── __init__.py
│   ├── video.py               ← Video, VideoStatus enum
│   ├── canal.py               ← Canal, CanalConfig, ChannelDNA
│   └── canal_candidato.py     ← CanalCandidato, MetricasCanal
├── services/
│   ├── __init__.py
│   ├── db.py                  ← DatabaseInterface (ABC)
│   ├── sheets_impl.py         ← Google Sheets implementation
│   ├── drive.py               ← Google Drive upload/download
│   ├── channel_discovery.py   ← YouTube API + scoring de canais
│   ├── scraper.py             ← yt-dlp wrapper
│   ├── transcritor.py         ← Whisper local
│   ├── vidiq_scraper.py       ← browser-use + VidIQ
│   ├── analisador.py          ← GPT-4o Vision
│   ├── roteirista.py          ← GPT-4o texto + DNA
│   ├── thumbnail.py           ← DALL-E 3
│   ├── narrador.py            ← ElevenLabs
│   ├── editor.py              ← Shotstack
│   └── publicador.py          ← YouTube Data API v3
└── routes/
    ├── __init__.py
    ├── auth.py                ← POST /auth/login
    ├── descoberta.py          ← POST /descobrir-canais, POST /canais/{id}/keywords
    ├── mineracao.py           ← POST /canais/{id}/minerar, GET candidatos, POST aprovar
    ├── analise.py             ← POST /canais/{id}/analisar/{video_id}
    ├── producao.py            ← POST /canais/{id}/produzir/{video_id}
    ├── publicacao.py          ← POST /canais/{id}/publicar/{video_id}
    └── canais.py              ← GET/PUT config + DNA

tests/
├── conftest.py                ← fixtures: test client, mock services
├── test_auth.py
├── test_channel_discovery.py
├── test_mining.py
├── test_analise.py
└── test_producao.py

canais/
└── mofmoney/
    ├── config.json
    └── channel_dna.json

templates/
├── whiteboard/
│   ├── shotstack.json
│   └── prompt_roteiro.txt
├── talking_head/
│   ├── shotstack.json
│   └── prompt_roteiro.txt
└── slides/
    ├── shotstack.json
    └── prompt_roteiro.txt

temp/                          ← arquivos temporários (gitignored)
credentials/                   ← google_credentials.json (gitignored)
requirements.txt
.env
.env.example
.gitignore
pytest.ini
```

---

### Task 1: GitHub Repo + Estrutura Base

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`

- [ ] **Step 1: Criar repo YTDARK no GitHub (Simplobot1)**

```bash
cd "C:\Users\ricar\projetos\YT DARK"
gh repo create Simplobot1/YTDARK --public --description "Sistema de mineração, análise e produção de vídeos para YouTube"
git init
git remote add origin https://github.com/Simplobot1/YTDARK.git
```

- [ ] **Step 2: Criar .gitignore**

```
# Arquivo: .gitignore
__pycache__/
*.py[cod]
.env
credentials/
temp/
*.mp3
*.mp4
*.json.bak
.pytest_cache/
.venv/
node_modules/
.next/
dist/
```

- [ ] **Step 3: Criar requirements.txt**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0

# YouTube & Video
yt-dlp>=2024.1.0
ffmpeg-python>=0.2.0
openai-whisper>=20240930

# AI
openai>=1.50.0
langchain-openai>=0.2.0
browser-use>=0.1.0
playwright>=1.40.0

# Google
google-auth>=2.30.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.140.0
gspread>=6.0.0

# Production
elevenlabs>=1.0.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9

# Testing
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-mock>=3.14.0
```

- [ ] **Step 4: Criar .env.example**

```
# Arquivo: .env.example
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=...
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
SHOTSTACK_API_KEY=...
SHOTSTACK_ENV=v1
JWT_SECRET=troque-por-string-aleatoria-longa
USERS=admin@email.com:senha123
```

- [ ] **Step 5: Criar pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 6: Criar app/config.py**

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str = ""
    youtube_api_key: str = ""
    google_credentials_path: str = "credentials/google_credentials.json"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    shotstack_api_key: str = ""
    shotstack_env: str = "v1"
    jwt_secret: str = "dev-secret"
    users: str = "admin@email.com:admin123"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 7: Criar app/main.py**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, descoberta, mineracao, analise, producao, publicacao, canais

app = FastAPI(
    title="YT DARK API",
    description="Sistema de mineração, análise e produção de vídeos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(descoberta.router, tags=["Descoberta"])
app.include_router(mineracao.router, prefix="/canais", tags=["Mineração"])
app.include_router(analise.router, prefix="/canais", tags=["Análise"])
app.include_router(producao.router, prefix="/canais", tags=["Produção"])
app.include_router(publicacao.router, prefix="/canais", tags=["Publicação"])
app.include_router(canais.router, prefix="/canais", tags=["Canais"])

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

- [ ] **Step 8: Criar __init__.py em todos os pacotes**

```bash
mkdir -p app/models app/services app/routes tests
touch app/__init__.py app/models/__init__.py app/services/__init__.py app/routes/__init__.py tests/__init__.py
```

- [ ] **Step 9: Criar arquivos __init__.py de rotas (stubs temporários)**

```python
# Criar cada arquivo abaixo com conteúdo mínimo para o app subir:
# app/routes/auth.py, descoberta.py, mineracao.py, analise.py, producao.py, publicacao.py, canais.py

from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 10: Instalar dependências e testar se o servidor sobe**

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Acessa http://localhost:8000/health — esperado: `{"status":"ok","version":"1.0.0"}`
Acessa http://localhost:8000/docs — Swagger UI deve carregar.

- [ ] **Step 11: Commit inicial**

```bash
git add .
git commit -m "feat: setup inicial FastAPI + estrutura de pastas"
git push -u origin main
```

---

### Task 2: Modelos de Dados

**Files:**
- Create: `app/models/video.py`
- Create: `app/models/canal.py`
- Create: `app/models/canal_candidato.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Criar app/models/video.py**

```python
# app/models/video.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class VideoStatus(str, Enum):
    CANDIDATO = "candidato"
    APROVADO = "aprovado"
    MINERADO = "minerado"
    ANALISADO = "analisado"
    ROTEIRO_GERADO = "roteiro_gerado"
    AUDIO_GERADO = "audio_gerado"
    VIDEO_PRONTO = "video_pronto"
    PUBLICADO = "publicado"

class Video(BaseModel):
    video_id: str
    titulo: str
    canal_fonte: str
    views: int
    data_pub: str
    duracao_min: float
    tipo: str = "whiteboard"
    score: float = 0.0
    status: VideoStatus = VideoStatus.CANDIDATO
    transcricao: Optional[str] = None
    analise: Optional[dict] = None
    roteiro_path: Optional[str] = None
    audio_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    video_path: Optional[str] = None
    drive_link: Optional[str] = None
    yt_link: Optional[str] = None
```

- [ ] **Step 2: Criar app/models/canal.py**

```python
# app/models/canal.py
from pydantic import BaseModel
from typing import List, Optional

class FiltrosMineracao(BaseModel):
    min_views: int = 50000
    max_dias: int = 30
    duracao_min_min: float = 8.0
    duracao_max_min: float = 20.0
    sem_legenda_pt: bool = True

class Agendamento(BaseModel):
    mineracao: str = "0 8 * * 1"
    producao: str = "0 10 * * 2"

class CanalConfig(BaseModel):
    canal_id: str
    youtube_handle: str
    idioma: str = "en"
    nicho_keywords: List[str] = []
    canais_fonte: List[str] = []
    tipo_video_padrao: str = "whiteboard"
    tipos_video_suportados: List[str] = ["whiteboard", "talking_head"]
    elevenlabs_voice_id: str = ""
    google_sheets_id: str = ""
    google_drive_folder_id: str = ""
    filtros_mineracao: FiltrosMineracao = FiltrosMineracao()

class ChannelDNA(BaseModel):
    estilo_visual: str = "whiteboard"
    tom_voz: str = "casual and educational"
    paleta_cores: List[str] = ["#FF6B35", "#FFFFFF", "#2C3E50"]
    intro_max_sec: int = 30
    hook_style: str = "bold question or shocking stat"
    num_pontos: int = 5
    cta_style: str = "subscribe + next video suggestion"
    thumbnail_formula: str = "bold text left + visual right"
    thumbnail_fonte: str = "Montserrat Bold"
    titulo_formula: str = "[Number] Ways to [Benefit] (No [Common Excuse])"
    duracao_alvo_min: int = 12
```

- [ ] **Step 3: Criar app/models/canal_candidato.py**

```python
# app/models/canal_candidato.py
from pydantic import BaseModel
from typing import Optional

class MetricasCanal(BaseModel):
    subscribers: int
    avg_views: float
    engagement_rate: float
    upload_freq_mensal: float
    avg_duration_min: float
    momentum: str  # "crescendo" | "estavel" | "declinando"

class CanalCandidato(BaseModel):
    handle: str
    nome: str
    channel_id: str
    metricas: MetricasCanal
    score: float
    melhor_video_recente: Optional[dict] = None
    adicionado: bool = False
```

- [ ] **Step 4: Criar tests/test_models.py**

```python
# tests/test_models.py
from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig, ChannelDNA
from app.models.canal_candidato import CanalCandidato, MetricasCanal

def test_video_default_status():
    v = Video(video_id="abc123", titulo="Test", canal_fonte="@test",
              views=100000, data_pub="2026-05-01", duracao_min=12.5)
    assert v.status == VideoStatus.CANDIDATO
    assert v.score == 0.0

def test_video_status_enum_values():
    assert VideoStatus.CANDIDATO == "candidato"
    assert VideoStatus.PUBLICADO == "publicado"

def test_canal_config_defaults():
    c = CanalConfig(canal_id="test", youtube_handle="@test")
    assert c.idioma == "en"
    assert c.tipo_video_padrao == "whiteboard"
    assert c.filtros_mineracao.min_views == 50000

def test_channel_dna_defaults():
    dna = ChannelDNA()
    assert dna.num_pontos == 5
    assert len(dna.paleta_cores) == 3

def test_canal_candidato_score():
    m = MetricasCanal(subscribers=500000, avg_views=120000,
                      engagement_rate=4.5, upload_freq_mensal=8,
                      avg_duration_min=14, momentum="crescendo")
    c = CanalCandidato(handle="@test", nome="Test Channel",
                       channel_id="UC123", metricas=m, score=87.5)
    assert c.score == 87.5
    assert not c.adicionado
```

- [ ] **Step 5: Rodar testes**

```bash
pytest tests/test_models.py -v
```
Esperado: 5 testes passando.

- [ ] **Step 6: Commit**

```bash
git add app/models/ tests/test_models.py
git commit -m "feat: modelos de dados (Video, Canal, ChannelDNA, CanalCandidato)"
```

---

### Task 3: Auth (JWT)

**Files:**
- Create: `app/auth.py`
- Modify: `app/routes/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Criar app/auth.py**

```python
# app/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def _get_users() -> dict:
    settings = get_settings()
    users = {}
    for entry in settings.users.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 2:
            users[parts[0]] = parts[1]
    return users

def verify_password(plain: str, stored: str) -> bool:
    try:
        return pwd_context.verify(plain, stored)
    except Exception:
        return plain == stored  # fallback para senha plain em dev

def create_token(email: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": email, "exp": expire}, settings.jwt_secret, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return email
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
```

- [ ] **Step 2: Implementar app/routes/auth.py**

```python
# app/routes/auth.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.auth import verify_password, create_token, _get_users

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    senha: str

class LoginResponse(BaseModel):
    token: str
    email: str

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    users = _get_users()
    stored = users.get(body.email)
    if not stored or not verify_password(body.senha, stored):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_token(body.email)
    return LoginResponse(token=token, email=body.email)
```

- [ ] **Step 3: Criar tests/conftest.py**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 4: Criar tests/test_auth.py**

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

def test_login_sucesso():
    with patch("app.routes.auth._get_users", return_value={"admin@test.com": "senha123"}):
        with patch("app.routes.auth.verify_password", return_value=True):
            resp = client.post("/auth/login", json={"email": "admin@test.com", "senha": "senha123"})
    assert resp.status_code == 200
    assert "token" in resp.json()

def test_login_credenciais_invalidas():
    with patch("app.routes.auth._get_users", return_value={"admin@test.com": "outrasenha"}):
        with patch("app.routes.auth.verify_password", return_value=False):
            resp = client.post("/auth/login", json={"email": "admin@test.com", "senha": "errada"})
    assert resp.status_code == 401

def test_health_sem_auth():
    resp = client.get("/health")
    assert resp.status_code == 200
```

- [ ] **Step 5: Rodar testes**

```bash
pytest tests/test_auth.py -v
```
Esperado: 3 testes passando.

- [ ] **Step 6: Commit**

```bash
git add app/auth.py app/routes/auth.py tests/test_auth.py tests/conftest.py
git commit -m "feat: JWT auth (login, token, verify)"
```

---

### Task 4: Camada de Dados (DB Interface + Google Sheets)

**Files:**
- Create: `app/services/db.py`
- Create: `app/services/sheets_impl.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Criar app/services/db.py**

```python
# app/services/db.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato

class DatabaseInterface(ABC):
    @abstractmethod
    def salvar_video(self, canal_id: str, video: Video) -> None: ...

    @abstractmethod
    def listar_candidatos(self, canal_id: str) -> List[Video]: ...

    @abstractmethod
    def atualizar_status(self, canal_id: str, video_id: str, status: VideoStatus) -> None: ...

    @abstractmethod
    def atualizar_video(self, canal_id: str, video: Video) -> None: ...

    @abstractmethod
    def buscar_video(self, canal_id: str, video_id: str) -> Optional[Video]: ...

    @abstractmethod
    def salvar_candidato_canal(self, canal_id: str, candidato: CanalCandidato) -> None: ...

    @abstractmethod
    def listar_candidatos_canal(self, canal_id: str) -> List[CanalCandidato]: ...

    @abstractmethod
    def salvar_keyword(self, canal_id: str, termo: str, volume: int, competition: float, seo_score: float) -> None: ...
```

- [ ] **Step 2: Criar app/services/sheets_impl.py**

```python
# app/services/sheets_impl.py
import json
from typing import List, Optional
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from app.services.db import DatabaseInterface
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

class SheetsDatabase(DatabaseInterface):
    def __init__(self, sheets_id: str):
        settings = get_settings()
        creds = Credentials.from_service_account_file(settings.google_credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(sheets_id)

    def _get_or_create_tab(self, nome: str, headers: List[str]):
        try:
            return self.sheet.worksheet(nome)
        except gspread.WorksheetNotFound:
            ws = self.sheet.add_worksheet(title=nome, rows=1000, cols=len(headers))
            ws.append_row(headers)
            return ws

    def salvar_video(self, canal_id: str, video: Video) -> None:
        ws = self._get_or_create_tab("Pipeline", [
            "video_id","titulo","canal_fonte","views","data_pub",
            "tipo","score","status","transcricao","drive_link","yt_link"
        ])
        ws.append_row([
            video.video_id, video.titulo, video.canal_fonte, video.views,
            video.data_pub, video.tipo, video.score, video.status.value,
            video.transcricao or "", video.drive_link or "", video.yt_link or ""
        ])

    def listar_candidatos(self, canal_id: str) -> List[Video]:
        ws = self._get_or_create_tab("Pipeline", [
            "video_id","titulo","canal_fonte","views","data_pub",
            "tipo","score","status","transcricao","drive_link","yt_link"
        ])
        records = ws.get_all_records()
        return [
            Video(
                video_id=r["video_id"], titulo=r["titulo"], canal_fonte=r["canal_fonte"],
                views=int(r["views"]), data_pub=r["data_pub"], tipo=r["tipo"],
                score=float(r["score"]), status=VideoStatus(r["status"]),
                transcricao=r.get("transcricao") or None,
                drive_link=r.get("drive_link") or None,
                yt_link=r.get("yt_link") or None,
                duracao_min=0.0
            )
            for r in records
        ]

    def atualizar_status(self, canal_id: str, video_id: str, status: VideoStatus) -> None:
        ws = self.sheet.worksheet("Pipeline")
        records = ws.get_all_records()
        for i, r in enumerate(records, start=2):
            if r["video_id"] == video_id:
                status_col = ws.find("status").col
                ws.update_cell(i, status_col, status.value)
                return

    def atualizar_video(self, canal_id: str, video: Video) -> None:
        self.atualizar_status(canal_id, video.video_id, video.status)

    def buscar_video(self, canal_id: str, video_id: str) -> Optional[Video]:
        videos = self.listar_candidatos(canal_id)
        return next((v for v in videos if v.video_id == video_id), None)

    def salvar_candidato_canal(self, canal_id: str, candidato: CanalCandidato) -> None:
        ws = self._get_or_create_tab("Canais Candidatos", [
            "handle","nome","channel_id","subscribers","avg_views",
            "engagement_rate","upload_freq","avg_duration","momentum","score","adicionado"
        ])
        ws.append_row([
            candidato.handle, candidato.nome, candidato.channel_id,
            candidato.metricas.subscribers, candidato.metricas.avg_views,
            candidato.metricas.engagement_rate, candidato.metricas.upload_freq_mensal,
            candidato.metricas.avg_duration_min, candidato.metricas.momentum,
            candidato.score, str(candidato.adicionado)
        ])

    def listar_candidatos_canal(self, canal_id: str) -> List[CanalCandidato]:
        try:
            ws = self.sheet.worksheet("Canais Candidatos")
        except gspread.WorksheetNotFound:
            return []
        records = ws.get_all_records()
        return [
            CanalCandidato(
                handle=r["handle"], nome=r["nome"], channel_id=r["channel_id"],
                metricas=MetricasCanal(
                    subscribers=int(r["subscribers"]), avg_views=float(r["avg_views"]),
                    engagement_rate=float(r["engagement_rate"]),
                    upload_freq_mensal=float(r["upload_freq"]),
                    avg_duration_min=float(r["avg_duration"]),
                    momentum=r["momentum"]
                ),
                score=float(r["score"]),
                adicionado=r["adicionado"] == "True"
            )
            for r in records
        ]

    def salvar_keyword(self, canal_id: str, termo: str, volume: int, competition: float, seo_score: float) -> None:
        ws = self._get_or_create_tab("Keywords", ["termo","volume","competition","seo_score","data"])
        ws.append_row([termo, volume, competition, seo_score, datetime.now().strftime("%Y-%m-%d")])
```

- [ ] **Step 3: Criar tests/test_db.py**

```python
# tests/test_db.py
import pytest
from unittest.mock import MagicMock, patch
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal

def _make_video():
    return Video(video_id="v001", titulo="Test Video", canal_fonte="@test",
                 views=100000, data_pub="2026-05-01", duracao_min=12.0,
                 score=85.0, status=VideoStatus.CANDIDATO)

def _make_candidato():
    m = MetricasCanal(subscribers=500000, avg_views=120000, engagement_rate=4.5,
                      upload_freq_mensal=8, avg_duration_min=14, momentum="crescendo")
    return CanalCandidato(handle="@testchan", nome="Test Chan",
                          channel_id="UC123", metricas=m, score=87.0)

@patch("app.services.sheets_impl.Credentials")
@patch("app.services.sheets_impl.gspread.authorize")
def test_salvar_video(mock_auth, mock_creds):
    mock_ws = MagicMock()
    mock_ws.find.return_value = MagicMock(col=8)
    mock_sheet = MagicMock()
    mock_sheet.worksheet.side_effect = lambda x: mock_ws
    mock_auth.return_value.open_by_key.return_value = mock_sheet
    mock_creds.from_service_account_file.return_value = MagicMock()

    from app.services.sheets_impl import SheetsDatabase
    db = SheetsDatabase("fake_id")
    db.salvar_video("mofmoney", _make_video())
    mock_ws.append_row.assert_called_once()

@patch("app.services.sheets_impl.Credentials")
@patch("app.services.sheets_impl.gspread.authorize")
def test_listar_candidatos_vazio(mock_auth, mock_creds):
    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = []
    mock_sheet = MagicMock()
    mock_sheet.worksheet.return_value = mock_ws
    mock_auth.return_value.open_by_key.return_value = mock_sheet
    mock_creds.from_service_account_file.return_value = MagicMock()

    from app.services.sheets_impl import SheetsDatabase
    db = SheetsDatabase("fake_id")
    result = db.listar_candidatos("mofmoney")
    assert result == []
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_db.py -v
```
Esperado: 2 testes passando.

- [ ] **Step 5: Commit**

```bash
git add app/services/db.py app/services/sheets_impl.py tests/test_db.py
git commit -m "feat: camada de dados (DatabaseInterface + SheetsDatabase)"
```

---

### Task 5: Google Drive Service

**Files:**
- Create: `app/services/drive.py`

- [ ] **Step 1: Criar app/services/drive.py**

```python
# app/services/drive.py
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from app.config import get_settings
import io

SCOPES = ["https://www.googleapis.com/auth/drive"]

def _get_service():
    settings = get_settings()
    creds = Credentials.from_service_account_file(settings.google_credentials_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def upload_file(local_path: str, drive_folder_id: str, mime_type: str = "application/octet-stream") -> str:
    """Faz upload de um arquivo para o Drive e retorna o link público."""
    service = _get_service()
    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [drive_folder_id]
    }
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")
    service.permissions().create(fileId=file_id, body={"type": "anyone", "role": "reader"}).execute()
    return f"https://drive.google.com/file/d/{file_id}/view"

def download_file(file_id: str, dest_path: str) -> str:
    """Baixa um arquivo do Drive para o caminho local."""
    service = _get_service()
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest_path

def get_folder_id_from_link(link: str) -> str:
    """Extrai o file_id de um link do Drive."""
    return link.split("/d/")[1].split("/")[0]
```

- [ ] **Step 2: Commit**

```bash
git add app/services/drive.py
git commit -m "feat: Google Drive service (upload, download)"
```

---

### Task 6: Configurações dos Canais (JSON)

**Files:**
- Create: `canais/mofmoney/config.json`
- Create: `canais/mofmoney/channel_dna.json`
- Create: `app/services/canal_config.py`
- Modify: `app/routes/canais.py`

- [ ] **Step 1: Criar canais/mofmoney/config.json**

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
    "duracao_min_min": 8.0,
    "duracao_max_min": 20.0,
    "sem_legenda_pt": true
  }
}
```

- [ ] **Step 2: Criar canais/mofmoney/channel_dna.json**

```json
{
  "estilo_visual": "whiteboard",
  "tom_voz": "casual and educational",
  "paleta_cores": ["#FF6B35", "#FFFFFF", "#2C3E50"],
  "intro_max_sec": 30,
  "hook_style": "bold question or shocking stat",
  "num_pontos": 5,
  "cta_style": "subscribe + next video suggestion",
  "thumbnail_formula": "bold text left + visual right",
  "thumbnail_fonte": "Montserrat Bold",
  "titulo_formula": "[Number] Ways to [Benefit] (No [Common Excuse])",
  "duracao_alvo_min": 12
}
```

- [ ] **Step 3: Criar app/services/canal_config.py**

```python
# app/services/canal_config.py
import json
import os
from app.models.canal import CanalConfig, ChannelDNA

CANAIS_DIR = "canais"

def listar_canais() -> list[str]:
    if not os.path.exists(CANAIS_DIR):
        return []
    return [d for d in os.listdir(CANAIS_DIR) if os.path.isdir(os.path.join(CANAIS_DIR, d))]

def get_config(canal_id: str) -> CanalConfig:
    path = os.path.join(CANAIS_DIR, canal_id, "config.json")
    with open(path) as f:
        return CanalConfig(**json.load(f))

def save_config(canal_id: str, config: CanalConfig) -> None:
    path = os.path.join(CANAIS_DIR, canal_id, "config.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

def get_dna(canal_id: str) -> ChannelDNA:
    path = os.path.join(CANAIS_DIR, canal_id, "channel_dna.json")
    with open(path) as f:
        return ChannelDNA(**json.load(f))

def save_dna(canal_id: str, dna: ChannelDNA) -> None:
    path = os.path.join(CANAIS_DIR, canal_id, "channel_dna.json")
    with open(path, "w") as f:
        json.dump(dna.model_dump(), f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Implementar app/routes/canais.py**

```python
# app/routes/canais.py
from fastapi import APIRouter, HTTPException
from app.models.canal import CanalConfig, ChannelDNA
from app.services.canal_config import listar_canais, get_config, save_config, get_dna, save_dna

router = APIRouter()

@router.get("/")
async def get_canais():
    return {"canais": listar_canais()}

@router.get("/{canal_id}/config")
async def get_canal_config(canal_id: str):
    try:
        return get_config(canal_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Canal '{canal_id}' não encontrado")

@router.put("/{canal_id}/config")
async def update_canal_config(canal_id: str, config: CanalConfig):
    save_config(canal_id, config)
    return {"ok": True}

@router.get("/{canal_id}/dna")
async def get_canal_dna(canal_id: str):
    try:
        return get_dna(canal_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"DNA do canal '{canal_id}' não encontrado")

@router.put("/{canal_id}/dna")
async def update_canal_dna(canal_id: str, dna: ChannelDNA):
    save_dna(canal_id, dna)
    return {"ok": True}
```

- [ ] **Step 5: Testar endpoints**

```bash
uvicorn app.main:app --reload
# Em outro terminal:
curl http://localhost:8000/canais/
curl http://localhost:8000/canais/mofmoney/config
curl http://localhost:8000/canais/mofmoney/dna
```

- [ ] **Step 6: Commit**

```bash
git add canais/ app/services/canal_config.py app/routes/canais.py
git commit -m "feat: configuração de canais (config.json + channel_dna.json + endpoints)"
```

---

### Task 7: Channel Discovery Service

**Files:**
- Create: `app/services/channel_discovery.py`
- Modify: `app/routes/descoberta.py`
- Create: `tests/test_channel_discovery.py`

- [ ] **Step 1: Criar app/services/channel_discovery.py**

```python
# app/services/channel_discovery.py
from typing import List, Optional
from googleapiclient.discovery import build
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings
from datetime import datetime, timedelta
import yt_dlp
import statistics

def _get_yt_service():
    return build("youtube", "v3", developerKey=get_settings().youtube_api_key)

def _calc_score(m: MetricasCanal) -> float:
    """Score = avg_views(40%) + engagement(30%) + upload_freq(20%) + momentum(10%)"""
    norm_views = min(m.avg_views / 500000, 1.0) * 40
    norm_eng = min(m.engagement_rate / 10.0, 1.0) * 30
    norm_freq = min(m.upload_freq_mensal / 12.0, 1.0) * 20
    norm_momentum = {"crescendo": 10, "estavel": 5, "declinando": 0}.get(m.momentum, 5)
    return round(norm_views + norm_eng + norm_freq + norm_momentum, 2)

def _get_channel_metrics(service, channel_id: str) -> Optional[MetricasCanal]:
    """Busca as métricas de um canal via YouTube API."""
    resp = service.channels().list(part="statistics,snippet", id=channel_id).execute()
    items = resp.get("items", [])
    if not items:
        return None
    stats = items[0]["statistics"]
    subscribers = int(stats.get("subscriberCount", 0))

    videos_resp = service.search().list(
        part="id", channelId=channel_id, type="video",
        order="date", maxResults=20
    ).execute()
    video_ids = [i["id"]["videoId"] for i in videos_resp.get("items", [])]
    if not video_ids:
        return None

    vids_resp = service.videos().list(
        part="statistics,contentDetails", id=",".join(video_ids)
    ).execute()

    views_list, eng_list, durations = [], [], []
    pub_dates = []
    for v in vids_resp.get("items", []):
        s = v["statistics"]
        views = int(s.get("viewCount", 0))
        likes = int(s.get("likeCount", 0))
        comments = int(s.get("commentCount", 0))
        views_list.append(views)
        eng_list.append((likes + comments) / max(views, 1) * 100)
        dur = v["contentDetails"]["duration"]  # ISO 8601
        mins = _parse_duration_to_min(dur)
        durations.append(mins)

    search_resp = service.search().list(
        part="snippet", channelId=channel_id, type="video",
        order="date", maxResults=4,
        publishedAfter=(datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ).execute()
    upload_freq = len(search_resp.get("items", []))

    avg_views_recent = statistics.mean(views_list[:5]) if views_list else 0
    avg_views_all = statistics.mean(views_list) if views_list else 0
    momentum = "crescendo" if avg_views_recent > avg_views_all * 1.1 else (
        "declinando" if avg_views_recent < avg_views_all * 0.9 else "estavel"
    )

    return MetricasCanal(
        subscribers=subscribers,
        avg_views=round(statistics.mean(views_list), 0) if views_list else 0,
        engagement_rate=round(statistics.mean(eng_list), 2) if eng_list else 0,
        upload_freq_mensal=upload_freq,
        avg_duration_min=round(statistics.mean(durations), 1) if durations else 0,
        momentum=momentum,
    )

def _parse_duration_to_min(iso_duration: str) -> float:
    """Converte PT12M30S → 12.5 minutos."""
    import re
    h = int(re.search(r"(\d+)H", iso_duration).group(1)) if "H" in iso_duration else 0
    m = int(re.search(r"(\d+)M", iso_duration).group(1)) if "M" in iso_duration else 0
    s = int(re.search(r"(\d+)S", iso_duration).group(1)) if "S" in iso_duration else 0
    return h * 60 + m + s / 60

def _get_related_channels_ ytdlp(seed_handle: str) -> List[str]:
    """Usa yt-dlp para extrair canais relacionados/featured do seed."""
    url = f"https://www.youtube.com/{seed_handle}/channels"
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", []) if info else []
            return [e.get("url", "") for e in entries if e.get("url")][:20]
        except Exception:
            return []

def discover_channels(
    estrategia: str,
    nicho: str,
    idioma: str,
    filtros: dict,
    top_n: int = 20,
    seed_channel: Optional[str] = None,
) -> List[CanalCandidato]:
    service = _get_yt_service()
    channel_ids = []

    if estrategia == "seed" and seed_channel:
        related_urls = _get_related_channels_ytdlp(seed_channel)
        for url in related_urls:
            if "channel/" in url:
                channel_ids.append(url.split("channel/")[-1])
            elif "@" in url:
                r = service.search().list(part="snippet", q=url, type="channel", maxResults=1).execute()
                for item in r.get("items", []):
                    channel_ids.append(item["snippet"]["channelId"])
    else:
        resp = service.search().list(
            part="snippet", q=nicho, type="channel",
            relevanceLanguage=idioma, maxResults=30
        ).execute()
        channel_ids = [i["snippet"]["channelId"] for i in resp.get("items", [])]

    candidatos = []
    for cid in channel_ids:
        metricas = _get_channel_metrics(service, cid)
        if not metricas:
            continue

        f = filtros
        if metricas.subscribers < f.get("subscribers_min", 0):
            continue
        if metricas.subscribers > f.get("subscribers_max", 999999999):
            continue
        if metricas.avg_views < f.get("avg_views_min", 0):
            continue
        if metricas.upload_freq_mensal < f.get("upload_freq_min", 0):
            continue
        if metricas.avg_duration_min < f.get("avg_duration_min_min", 0):
            continue
        if metricas.avg_duration_min > f.get("avg_duration_max_min", 999):
            continue

        resp = service.channels().list(part="snippet", id=cid).execute()
        snippet = resp["items"][0]["snippet"]
        handle = snippet.get("customUrl", f"@{snippet['title'].replace(' ','')}")
        score = _calc_score(metricas)

        candidatos.append(CanalCandidato(
            handle=handle, nome=snippet["title"], channel_id=cid,
            metricas=metricas, score=score
        ))

    candidatos.sort(key=lambda c: c.score, reverse=True)
    return candidatos[:top_n]
```

- [ ] **Step 2: Implementar app/routes/descoberta.py**

```python
# app/routes/descoberta.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.auth import verify_token
from app.services.channel_discovery import discover_channels
from app.models.canal_candidato import CanalCandidato

router = APIRouter()

class DescobertaRequest(BaseModel):
    estrategia: str = "categoria"
    seed_channel: Optional[str] = None
    nicho: str = "personal finance"
    idioma: str = "en"
    filtros: dict = {
        "subscribers_min": 100000,
        "subscribers_max": 3000000,
        "avg_views_min": 50000,
        "upload_freq_min": 4,
        "avg_duration_min_min": 8,
        "avg_duration_max_min": 20,
    }
    top_n: int = 20

@router.post("/descobrir-canais", response_model=List[CanalCandidato])
async def descobrir_canais(body: DescobertaRequest, _=Depends(verify_token)):
    return discover_channels(
        estrategia=body.estrategia,
        nicho=body.nicho,
        idioma=body.idioma,
        filtros=body.filtros,
        top_n=body.top_n,
        seed_channel=body.seed_channel,
    )
```

- [ ] **Step 3: Criar tests/test_channel_discovery.py**

```python
# tests/test_channel_discovery.py
from app.services.channel_discovery import _calc_score, _parse_duration_to_min
from app.models.canal_candidato import MetricasCanal

def test_parse_duration_12m30s():
    assert _parse_duration_to_min("PT12M30S") == 12.5

def test_parse_duration_1h5m():
    assert _parse_duration_to_min("PT1H5M") == 65.0

def test_parse_duration_only_minutes():
    assert _parse_duration_to_min("PT8M") == 8.0

def test_calc_score_high_performer():
    m = MetricasCanal(subscribers=1000000, avg_views=400000,
                      engagement_rate=5.0, upload_freq_mensal=10,
                      avg_duration_min=14, momentum="crescendo")
    score = _calc_score(m)
    assert score > 70

def test_calc_score_low_performer():
    m = MetricasCanal(subscribers=50000, avg_views=5000,
                      engagement_rate=0.5, upload_freq_mensal=1,
                      avg_duration_min=5, momentum="declinando")
    score = _calc_score(m)
    assert score < 20

def test_calc_score_momentum_crescendo_maior():
    m_up = MetricasCanal(subscribers=500000, avg_views=100000,
                         engagement_rate=3.0, upload_freq_mensal=6,
                         avg_duration_min=12, momentum="crescendo")
    m_down = MetricasCanal(subscribers=500000, avg_views=100000,
                           engagement_rate=3.0, upload_freq_mensal=6,
                           avg_duration_min=12, momentum="declinando")
    assert _calc_score(m_up) > _calc_score(m_down)
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_channel_discovery.py -v
```
Esperado: 6 testes passando.

- [ ] **Step 5: Commit**

```bash
git add app/services/channel_discovery.py app/routes/descoberta.py tests/test_channel_discovery.py
git commit -m "feat: channel discovery por métricas (seed + categoria + scoring)"
```

---

### Task 8: yt-dlp Scraper + Whisper Transcriber

**Files:**
- Create: `app/services/scraper.py`
- Create: `app/services/transcritor.py`

- [ ] **Step 1: Criar app/services/scraper.py**

```python
# app/services/scraper.py
import os
import yt_dlp
from typing import Optional

TEMP_DIR = "temp"

def _ensure_temp():
    os.makedirs(TEMP_DIR, exist_ok=True)

def get_video_metadata(video_url: str) -> dict:
    opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(video_url, download=False)

def download_audio(video_id: str) -> str:
    """Baixa o áudio de um vídeo para temp/. Retorna caminho do .mp3."""
    _ensure_temp()
    out_path = os.path.join(TEMP_DIR, f"{video_id}.mp3")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(TEMP_DIR, f"{video_id}.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return out_path

def extract_frames(video_id: str, num_frames: int = 8) -> list[str]:
    """Extrai frames-chave de um vídeo. Retorna lista de caminhos de imagens."""
    import subprocess
    _ensure_temp()
    video_path = os.path.join(TEMP_DIR, f"{video_id}.mp4")
    opts = {"format": "best[height<=720]", "outtmpl": video_path, "quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    frames_dir = os.path.join(TEMP_DIR, f"{video_id}_frames")
    os.makedirs(frames_dir, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-i", video_path, "-vf", f"fps=1/{60//num_frames}",
        os.path.join(frames_dir, "frame_%03d.jpg"), "-y", "-loglevel", "quiet"
    ], check=True)

    frames = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".jpg")])
    return frames[:num_frames]

def cleanup_temp(video_id: str):
    """Remove arquivos temporários do vídeo."""
    import shutil
    for path in [
        os.path.join(TEMP_DIR, f"{video_id}.mp3"),
        os.path.join(TEMP_DIR, f"{video_id}.mp4"),
        os.path.join(TEMP_DIR, f"{video_id}_frames"),
    ]:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
```

- [ ] **Step 2: Criar app/services/transcritor.py**

```python
# app/services/transcritor.py
import whisper
import os

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")  # base = bom equilíbrio velocidade/qualidade
    return _model

def transcrever(audio_path: str, idioma: str = "en") -> str:
    """Transcreve um arquivo de áudio com Whisper local. Retorna o texto."""
    model = _get_model()
    result = model.transcribe(audio_path, language=idioma, fp16=False)
    return result["text"].strip()
```

- [ ] **Step 3: Commit**

```bash
git add app/services/scraper.py app/services/transcritor.py
git commit -m "feat: yt-dlp scraper (metadados, áudio, frames) + Whisper local"
```

---

### Task 9: VidIQ Keyword Research

**Files:**
- Create: `app/services/vidiq_scraper.py`
- Modify: `app/routes/descoberta.py`

- [ ] **Step 1: Criar app/services/vidiq_scraper.py**

```python
# app/services/vidiq_scraper.py
import asyncio
import json
import re
from typing import List
from langchain_openai import ChatOpenAI
from app.config import get_settings

async def buscar_keywords_vidiq(nicho: str, idioma: str = "en") -> List[dict]:
    """Usa browser-use para extrair keywords do VidIQ."""
    try:
        from browser_use import Agent
    except ImportError:
        return _fallback_keywords(nicho)

    settings = get_settings()
    llm = ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key)
    agent = Agent(
        task=(
            f"Go to vidiq.com. If a login page appears, skip it and go directly to "
            f"https://vidiq.com/keyword-research. In the search box, type '{nicho}' and press Enter. "
            f"Wait for results. Extract the top 15 keywords shown with: term, search volume, "
            f"competition score (0-100), and SEO score (0-100). "
            f"Return ONLY a JSON array like: "
            f'[{{"termo":"...", "volume":1000, "competition":45.0, "seo_score":72.0}}]'
        ),
        llm=llm,
    )
    result = await agent.run()

    try:
        text = str(result)
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return _fallback_keywords(nicho)

def _fallback_keywords(nicho: str) -> List[dict]:
    """Retorna keywords genéricas quando browser-use falha."""
    base = nicho.split()[0] if nicho else "finance"
    return [
        {"termo": f"how to {base}", "volume": 50000, "competition": 60.0, "seo_score": 55.0},
        {"termo": f"best {base} tips", "volume": 30000, "competition": 45.0, "seo_score": 68.0},
        {"termo": f"{base} for beginners", "volume": 80000, "competition": 70.0, "seo_score": 48.0},
    ]
```

- [ ] **Step 2: Adicionar endpoint de keywords em app/routes/descoberta.py**

```python
# Adicionar ao final de app/routes/descoberta.py
from app.services.vidiq_scraper import buscar_keywords_vidiq

class KeywordsRequest(BaseModel):
    nicho: str
    idioma: str = "en"

@router.post("/canais/{canal_id}/keywords")
async def keyword_research(canal_id: str, body: KeywordsRequest, _=Depends(verify_token)):
    keywords = await buscar_keywords_vidiq(body.nicho, body.idioma)
    return {"canal_id": canal_id, "nicho": body.nicho, "keywords": keywords}
```

- [ ] **Step 3: Commit**

```bash
git add app/services/vidiq_scraper.py app/routes/descoberta.py
git commit -m "feat: VidIQ keyword research via browser-use com fallback"
```

---

### Task 10: Serviço de Mineração + Score de Vídeos

**Files:**
- Create: `app/services/minerador.py`
- Modify: `app/routes/mineracao.py`
- Create: `tests/test_mining.py`

- [ ] **Step 1: Criar app/services/minerador.py**

```python
# app/services/minerador.py
from typing import List, Optional
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig
from app.config import get_settings
import re

def _parse_iso_duration_to_min(iso: str) -> float:
    h = int(re.search(r"(\d+)H", iso).group(1)) if "H" in iso else 0
    m = int(re.search(r"(\d+)M", iso).group(1)) if "M" in iso else 0
    s = int(re.search(r"(\d+)S", iso).group(1)) if "S" in iso else 0
    return h * 60 + m + s / 60

def _calc_video_score(views: int, likes: int, comments: int, duration_min: float,
                      canal_avg_views: float, keywords: List[str], titulo: str) -> float:
    views_ratio = min(views / max(canal_avg_views, 1), 3.0) / 3.0 * 40
    eng = (likes + comments) / max(views, 1) * 100
    engagement = min(eng / 10.0, 1.0) * 30
    titulo_lower = titulo.lower()
    keyword_hits = sum(1 for kw in keywords if kw.lower() in titulo_lower)
    keyword_fit = min(keyword_hits / max(len(keywords), 1), 1.0) * 20
    dna_fit = 10.0 if 8 <= duration_min <= 20 else 5.0
    return round(views_ratio + engagement + keyword_fit + dna_fit, 2)

def minerar_canal(config: CanalConfig, canal_avg_views: float = 100000) -> List[Video]:
    service = build("youtube", "v3", developerKey=get_settings().youtube_api_key)
    f = config.filtros_mineracao
    since = (datetime.utcnow() - timedelta(days=f.max_dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    videos = []

    for handle in config.canais_fonte:
        search_resp = service.search().list(
            part="snippet", q=handle.replace("@", ""),
            type="video", order="viewCount",
            publishedAfter=since,
            videoDuration="medium",
            relevanceLanguage=config.idioma,
            maxResults=10
        ).execute()

        video_ids = [i["id"]["videoId"] for i in search_resp.get("items", [])]
        if not video_ids:
            continue

        vids_resp = service.videos().list(
            part="statistics,contentDetails,snippet", id=",".join(video_ids)
        ).execute()

        for v in vids_resp.get("items", []):
            stats = v["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            duration_min = _parse_iso_duration_to_min(v["contentDetails"]["duration"])

            if views < f.min_views:
                continue
            if not (f.duracao_min_min <= duration_min <= f.duracao_max_min):
                continue

            score = _calc_video_score(
                views, likes, comments, duration_min,
                canal_avg_views, config.nicho_keywords, v["snippet"]["title"]
            )

            videos.append(Video(
                video_id=v["id"],
                titulo=v["snippet"]["title"],
                canal_fonte=handle,
                views=views,
                data_pub=v["snippet"]["publishedAt"][:10],
                duracao_min=round(duration_min, 1),
                tipo=config.tipo_video_padrao,
                score=score,
                status=VideoStatus.CANDIDATO,
            ))

    videos.sort(key=lambda v: v.score, reverse=True)
    return videos
```

- [ ] **Step 2: Implementar app/routes/mineracao.py**

```python
# app/routes/mineracao.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.minerador import minerar_canal
from app.services.canal_config import get_config, get_dna
from app.services.sheets_impl import SheetsDatabase
from app.models.video import VideoStatus

router = APIRouter()

def _get_db(canal_id: str) -> SheetsDatabase:
    config = get_config(canal_id)
    if not config.google_sheets_id:
        raise HTTPException(400, "google_sheets_id não configurado para este canal")
    return SheetsDatabase(config.google_sheets_id)

@router.post("/{canal_id}/minerar")
async def minerar(canal_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    videos = minerar_canal(config)
    db = _get_db(canal_id)
    for v in videos:
        db.salvar_video(canal_id, v)
    return {"minerados": len(videos), "videos": [v.model_dump() for v in videos]}

@router.get("/{canal_id}/candidatos")
async def listar_candidatos(canal_id: str, _=Depends(verify_token)):
    db = _get_db(canal_id)
    return db.listar_candidatos(canal_id)

@router.post("/{canal_id}/aprovar/{video_id}")
async def aprovar_video(canal_id: str, video_id: str, _=Depends(verify_token)):
    db = _get_db(canal_id)
    db.atualizar_status(canal_id, video_id, VideoStatus.APROVADO)
    return {"ok": True, "video_id": video_id, "status": "aprovado"}
```

- [ ] **Step 3: Criar tests/test_mining.py**

```python
# tests/test_mining.py
from app.services.minerador import _calc_video_score, _parse_iso_duration_to_min

def test_parse_duration_15min():
    assert _parse_iso_duration_to_min("PT15M") == 15.0

def test_parse_duration_1h10m30s():
    assert _parse_iso_duration_to_min("PT1H10M30S") == pytest.approx(70.5, 0.01)

def test_score_viral_video():
    score = _calc_video_score(
        views=500000, likes=20000, comments=1000,
        duration_min=14.0, canal_avg_views=100000,
        keywords=["personal finance", "investing"],
        titulo="5 Investing Mistakes to Avoid in 2026"
    )
    assert score > 60

def test_score_bad_video():
    score = _calc_video_score(
        views=1000, likes=10, comments=2,
        duration_min=3.0, canal_avg_views=100000,
        keywords=["personal finance"],
        titulo="Random Video"
    )
    assert score < 20

def test_score_keyword_match_aumenta_score():
    score_match = _calc_video_score(500000, 15000, 800, 13.0, 100000,
                                    ["personal finance"], "Personal Finance Tips")
    score_no_match = _calc_video_score(500000, 15000, 800, 13.0, 100000,
                                       ["personal finance"], "Random Title")
    assert score_match > score_no_match

import pytest
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_mining.py -v
```
Esperado: 5 testes passando.

- [ ] **Step 5: Commit**

```bash
git add app/services/minerador.py app/routes/mineracao.py tests/test_mining.py
git commit -m "feat: mineração de vídeos com score ponderado (views, engagement, keywords, DNA)"
```

---

### Task 11: GPT-4o Vision Analyzer

**Files:**
- Create: `app/services/analisador.py`
- Modify: `app/routes/analise.py`

- [ ] **Step 1: Criar app/services/analisador.py**

```python
# app/services/analisador.py
import base64
import json
import os
from typing import List
from openai import OpenAI
from app.config import get_settings

def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analisar_frames(frames: List[str], transcricao: str, titulo: str) -> dict:
    """Analisa frames de um vídeo com GPT-4o Vision. Retorna estrutura de análise."""
    client = OpenAI(api_key=get_settings().openai_api_key)

    content = [
        {"type": "text", "text": (
            f"Você é um especialista em análise de conteúdo para YouTube.\n"
            f"Analise os frames deste vídeo intitulado '{titulo}'.\n"
            f"Transcrição parcial: {transcricao[:1000]}...\n\n"
            f"Retorne um JSON com:\n"
            f"- tipo_video: 'whiteboard' | 'talking_head' | 'slides'\n"
            f"- estrutura_roteiro: {{intro_segundos, num_pontos, tem_cta}}\n"
            f"- elementos_visuais: [lista de elementos observados]\n"
            f"- cores_dominantes: [lista de cores em hex]\n"
            f"- estilo_thumbnail: descrição do estilo visual\n"
            f"- tema_central: o tema principal do vídeo em 1 frase\n"
            f"- angulo_conteudo: qual o ângulo/perspectiva única deste vídeo\n"
            f"Responda APENAS com o JSON, sem texto extra."
        )}
    ]

    for frame_path in frames[:6]:
        img_b64 = _encode_image(frame_path)
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{img_b64}", "detail": "low"
        }})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
```

- [ ] **Step 2: Implementar app/routes/analise.py**

```python
# app/routes/analise.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.scraper import extract_frames, download_audio, cleanup_temp
from app.services.transcritor import transcrever
from app.services.analisador import analisar_frames
from app.services.drive import upload_file
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.models.video import VideoStatus
import os

router = APIRouter()

@router.post("/{canal_id}/analisar/{video_id}")
async def analisar_video(canal_id: str, video_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)
    if not video:
        raise HTTPException(404, f"Video {video_id} não encontrado")

    audio_path = download_audio(video_id)
    transcricao = transcrever(audio_path, config.idioma)
    frames = extract_frames(video_id)
    analise = analisar_frames(frames, transcricao, video.titulo)

    if config.google_drive_folder_id:
        for frame in frames:
            upload_file(frame, config.google_drive_folder_id, "image/jpeg")

    video.transcricao = transcricao
    video.analise = analise
    video.status = VideoStatus.ANALISADO
    db.atualizar_video(canal_id, video)
    cleanup_temp(video_id)

    return {"video_id": video_id, "analise": analise, "transcricao_preview": transcricao[:200]}

@router.get("/{canal_id}/analisados")
async def listar_analisados(canal_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    todos = db.listar_candidatos(canal_id)
    return [v for v in todos if v.status == VideoStatus.ANALISADO]
```

- [ ] **Step 3: Commit**

```bash
git add app/services/analisador.py app/routes/analise.py
git commit -m "feat: análise GPT-4o Vision (frames + transcrição Whisper → estrutura do vídeo)"
```

---

### Task 12: Geração de Roteiro + Thumbnail

**Files:**
- Create: `app/services/roteirista.py`
- Create: `app/services/thumbnail.py`
- Create: `templates/whiteboard/prompt_roteiro.txt`
- Create: `templates/talking_head/prompt_roteiro.txt`
- Create: `templates/slides/prompt_roteiro.txt`

- [ ] **Step 1: Criar templates/whiteboard/prompt_roteiro.txt**

```
Você é um roteirista especializado em vídeos de {idioma} sobre {nicho}.
Escreva um roteiro ORIGINAL e COMPLETO para um vídeo de YouTube no estilo WHITEBOARD.

TEMA INSPIRADOR (não copie — apenas se inspire): {tema_central}
ÂNGULO DO VÍDEO: {angulo_conteudo}
CANAL DNA:
- Tom de voz: {tom_voz}
- Fórmula de título: {titulo_formula}
- Número de pontos: {num_pontos}
- Hook style: {hook_style}
- CTA: {cta_style}
- Duração alvo: {duracao_alvo_min} minutos

ESTRUTURA OBRIGATÓRIA:
[TÍTULO] (usando a fórmula do DNA)
[HOOK] (máx {intro_max_sec} segundos — use o hook style definido)
[PONTO 1] título + narração completa (~2 min)
[PONTO 2] título + narração completa (~2 min)
[PONTO 3] título + narração completa (~2 min)
[PONTO 4] título + narração completa (~2 min)
[PONTO 5] título + narração completa (~2 min)
[CTA] narração completa do call-to-action

REGRAS:
- Escreva como se você fosse o apresentador narrando
- Use linguagem {tom_voz}
- O conteúdo deve ser 100% ORIGINAL — inspire-se no ângulo mas crie novo conteúdo
- Inclua dados e exemplos reais quando possível
```

- [ ] **Step 2: Criar templates/talking_head/prompt_roteiro.txt**

```
Você é um roteirista especializado em vídeos de {idioma} sobre {nicho}.
Escreva um roteiro ORIGINAL para um vídeo TALKING HEAD (apresentador em câmera).

TEMA INSPIRADOR (não copie): {tema_central}
ÂNGULO: {angulo_conteudo}

CANAL DNA:
- Tom: {tom_voz}
- Fórmula título: {titulo_formula}
- Pontos: {num_pontos}
- Hook: {hook_style}
- CTA: {cta_style}
- Duração: {duracao_alvo_min} min

ESTRUTURA:
[TÍTULO]
[HOOK] (câmera direta, {intro_max_sec}s)
[LOWER THIRD 1]: {ponto} — narração 2 min
[LOWER THIRD 2]: {ponto} — narração 2 min
[LOWER THIRD 3]: {ponto} — narração 2 min
[LOWER THIRD 4]: {ponto} — narração 2 min
[LOWER THIRD 5]: {ponto} — narração 2 min
[CTA] olhar direto para câmera
```

- [ ] **Step 3: Criar templates/slides/prompt_roteiro.txt**

```
Você é um roteirista especializado em vídeos de {idioma} sobre {nicho}.
Escreva um roteiro ORIGINAL para um vídeo em formato SLIDES (apresentação + narração).

TEMA INSPIRADOR (não copie): {tema_central}
ÂNGULO: {angulo_conteudo}

CANAL DNA:
- Tom: {tom_voz}
- Fórmula título: {titulo_formula}
- Pontos: {num_pontos}
- Duração: {duracao_alvo_min} min

ESTRUTURA:
[TÍTULO]
[SLIDE TÍTULO]: texto do slide + narração
[SLIDE 1 - {ponto}]: bullet points + narração 2 min
[SLIDE 2 - {ponto}]: bullet points + narração 2 min
[SLIDE 3 - {ponto}]: bullet points + narração 2 min
[SLIDE 4 - {ponto}]: bullet points + narração 2 min
[SLIDE 5 - {ponto}]: bullet points + narração 2 min
[SLIDE CTA]: texto + narração
```

- [ ] **Step 4: Criar app/services/roteirista.py**

```python
# app/services/roteirista.py
import os
from openai import OpenAI
from app.config import get_settings
from app.models.canal import ChannelDNA, CanalConfig

def _load_prompt_template(tipo_video: str) -> str:
    path = os.path.join("templates", tipo_video, "prompt_roteiro.txt")
    with open(path) as f:
        return f.read()

def gerar_roteiro(analise: dict, dna: ChannelDNA, config: CanalConfig) -> str:
    """Gera roteiro original baseado na análise do vídeo e no DNA do canal."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    tipo = analise.get("tipo_video", config.tipo_video_padrao)
    prompt_template = _load_prompt_template(tipo)

    prompt = prompt_template.format(
        idioma=config.idioma,
        nicho=" ".join(config.nicho_keywords[:3]),
        tema_central=analise.get("tema_central", ""),
        angulo_conteudo=analise.get("angulo_conteudo", ""),
        tom_voz=dna.tom_voz,
        titulo_formula=dna.titulo_formula,
        num_pontos=dna.num_pontos,
        hook_style=dna.hook_style,
        cta_style=dna.cta_style,
        duracao_alvo_min=dna.duracao_alvo_min,
        intro_max_sec=dna.intro_max_sec,
        ponto="[PONTO]",
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
    )
    return response.choices[0].message.content.strip()
```

- [ ] **Step 5: Criar app/services/thumbnail.py**

```python
# app/services/thumbnail.py
import os
import httpx
from openai import OpenAI
from app.config import get_settings
from app.models.canal import ChannelDNA

TEMP_DIR = "temp"

def gerar_thumbnail(titulo: str, dna: ChannelDNA, video_id: str) -> str:
    """Gera thumbnail original com DALL-E 3. Retorna caminho do arquivo."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    cores = " and ".join(dna.paleta_cores[:2])
    prompt = (
        f"YouTube thumbnail for a video titled '{titulo}'. "
        f"Style: {dna.thumbnail_formula}. "
        f"Colors: {cores}. "
        f"Font style: {dna.thumbnail_fonte}. "
        f"Clean, professional, high contrast. No text overlays. "
        f"Finance/money visual theme. 16:9 aspect ratio."
    )
    response = client.images.generate(
        model="dall-e-3", prompt=prompt,
        size="1792x1024", quality="standard", n=1
    )
    image_url = response.data[0].url
    os.makedirs(TEMP_DIR, exist_ok=True)
    dest = os.path.join(TEMP_DIR, f"{video_id}_thumbnail.jpg")
    with httpx.Client() as c:
        r = c.get(image_url)
        with open(dest, "wb") as f:
            f.write(r.content)
    return dest
```

- [ ] **Step 6: Commit**

```bash
git add app/services/roteirista.py app/services/thumbnail.py templates/
git commit -m "feat: roteirista GPT-4o com DNA do canal + thumbnail DALL-E 3"
```

---

### Task 13: ElevenLabs + Shotstack + Publicação

**Files:**
- Create: `app/services/narrador.py`
- Create: `app/services/editor.py`
- Create: `app/services/publicador.py`
- Create: `templates/whiteboard/shotstack.json`
- Modify: `app/routes/producao.py`
- Modify: `app/routes/publicacao.py`

- [ ] **Step 1: Criar app/services/narrador.py**

```python
# app/services/narrador.py
import os
from elevenlabs import ElevenLabs
from app.config import get_settings

TEMP_DIR = "temp"

def gerar_narracao(texto: str, video_id: str) -> str:
    """Gera narração em MP3 com ElevenLabs. Retorna caminho do arquivo."""
    settings = get_settings()
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    narration_only = _extract_narration(texto)
    audio = client.generate(
        text=narration_only,
        voice=settings.elevenlabs_voice_id or "Rachel",
        model="eleven_multilingual_v2",
    )
    os.makedirs(TEMP_DIR, exist_ok=True)
    dest = os.path.join(TEMP_DIR, f"{video_id}.mp3")
    with open(dest, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return dest

def _extract_narration(roteiro: str) -> str:
    """Remove marcações de estrutura, mantém só o texto narrado."""
    lines = []
    for line in roteiro.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        if stripped:
            lines.append(stripped)
    return " ".join(lines)
```

- [ ] **Step 2: Criar templates/whiteboard/shotstack.json**

```json
{
  "timeline": {
    "background": "#FFFFFF",
    "tracks": [
      {
        "clips": [
          {
            "asset": { "type": "audio", "src": "{{AUDIO_URL}}" },
            "start": 0,
            "length": "{{DURACAO}}"
          }
        ]
      },
      {
        "clips": [
          {
            "asset": {
              "type": "html",
              "html": "<p style='font-family:Montserrat,sans-serif;font-size:48px;font-weight:bold;color:#FF6B35;text-align:center'>{{TITULO}}</p>",
              "width": 1280,
              "height": 200
            },
            "position": "center",
            "start": 0,
            "length": 5
          }
        ]
      },
      {
        "clips": [
          {
            "asset": { "type": "image", "src": "{{THUMBNAIL_URL}}" },
            "start": 0,
            "length": "{{DURACAO}}",
            "opacity": 0.1
          }
        ]
      }
    ]
  },
  "output": {
    "format": "mp4",
    "resolution": "hd",
    "fps": 30
  }
}
```

- [ ] **Step 3: Criar app/services/editor.py**

```python
# app/services/editor.py
import json
import os
import time
import httpx
from app.config import get_settings

SHOTSTACK_BASE = "https://api.shotstack.io"

def _get_headers():
    settings = get_settings()
    env = settings.shotstack_env
    key = settings.shotstack_api_key
    return {
        "x-api-key": key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, env

def montar_video(tipo_template: str, audio_url: str, thumbnail_url: str,
                 titulo: str, duracao_sec: float, video_id: str) -> str:
    """Renderiza vídeo com Shotstack. Retorna URL do MP4 final."""
    template_path = os.path.join("templates", tipo_template, "shotstack.json")
    with open(template_path) as f:
        template = json.load(f)

    payload_str = json.dumps(template)
    payload_str = payload_str.replace("{{AUDIO_URL}}", audio_url)
    payload_str = payload_str.replace("{{THUMBNAIL_URL}}", thumbnail_url)
    payload_str = payload_str.replace("{{TITULO}}", titulo)
    payload_str = payload_str.replace('"{{DURACAO}}"', str(duracao_sec))
    payload = json.loads(payload_str)

    headers, env = _get_headers()
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{SHOTSTACK_BASE}/{env}/render", json=payload, headers=headers)
        resp.raise_for_status()
        render_id = resp.json()["response"]["id"]

    return _poll_render(render_id, headers, env)

def _poll_render(render_id: str, headers: dict, env: str) -> str:
    """Poll até render completar. Retorna URL do vídeo."""
    with httpx.Client(timeout=30) as client:
        for _ in range(60):
            time.sleep(10)
            resp = client.get(f"{SHOTSTACK_BASE}/{env}/render/{render_id}", headers=headers)
            data = resp.json()["response"]
            if data["status"] == "done":
                return data["url"]
            if data["status"] == "failed":
                raise RuntimeError(f"Shotstack render falhou: {data.get('error', 'unknown')}")
    raise TimeoutError("Shotstack render timeout após 10 minutos")
```

- [ ] **Step 4: Criar app/services/publicador.py**

```python
# app/services/publicador.py
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = "credentials/youtube_token.json"

def _get_youtube_service():
    settings = get_settings()
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(settings.google_credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def publicar_video(video_path: str, titulo: str, descricao: str,
                   tags: list[str], thumbnail_path: str) -> str:
    """Faz upload do vídeo no YouTube. Retorna o link do vídeo publicado."""
    youtube = _get_youtube_service()
    body = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "tags": tags,
            "categoryId": "27",
        },
        "status": {"privacyStatus": "private"},
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    video_id = response["id"]

    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()

    return f"https://www.youtube.com/watch?v={video_id}"
```

- [ ] **Step 5: Implementar app/routes/producao.py**

```python
# app/routes/producao.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.canal_config import get_config, get_dna
from app.services.sheets_impl import SheetsDatabase
from app.services.roteirista import gerar_roteiro
from app.services.thumbnail import gerar_thumbnail
from app.services.narrador import gerar_narracao
from app.services.editor import montar_video
from app.services.drive import upload_file
from app.models.video import VideoStatus
import os

router = APIRouter()

@router.post("/{canal_id}/produzir/{video_id}")
async def produzir_video(canal_id: str, video_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    dna = get_dna(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)

    if not video or not video.analise:
        raise HTTPException(400, "Vídeo precisa estar analisado antes de produzir")

    roteiro = gerar_roteiro(video.analise, dna, config)
    roteiro_path = f"temp/{video_id}_roteiro.txt"
    with open(roteiro_path, "w") as f:
        f.write(roteiro)
    roteiro_drive = upload_file(roteiro_path, config.google_drive_folder_id, "text/plain")
    video.status = VideoStatus.ROTEIRO_GERADO

    thumbnail_local = gerar_thumbnail(roteiro.split("\n")[0].replace("[TÍTULO]", "").strip(), dna, video_id)
    thumbnail_drive = upload_file(thumbnail_local, config.google_drive_folder_id, "image/jpeg")
    video.status = VideoStatus.ROTEIRO_GERADO

    audio_local = gerar_narracao(roteiro, video_id)
    audio_drive = upload_file(audio_local, config.google_drive_folder_id, "audio/mpeg")
    video.status = VideoStatus.AUDIO_GERADO

    from mutagen.mp3 import MP3
    duracao_sec = MP3(audio_local).info.length

    mp4_url = montar_video(
        tipo_template=video.analise.get("tipo_video", config.tipo_video_padrao),
        audio_url=audio_drive,
        thumbnail_url=thumbnail_drive,
        titulo=roteiro.split("\n")[0].replace("[TÍTULO]", "").strip(),
        duracao_sec=duracao_sec,
        video_id=video_id,
    )

    video.audio_path = audio_drive
    video.thumbnail_path = thumbnail_drive
    video.roteiro_path = roteiro_drive
    video.video_path = mp4_url
    video.status = VideoStatus.VIDEO_PRONTO
    db.atualizar_video(canal_id, video)

    return {
        "video_id": video_id,
        "status": "video_pronto",
        "mp4_url": mp4_url,
        "roteiro_drive": roteiro_drive,
        "thumbnail_drive": thumbnail_drive,
    }

@router.get("/{canal_id}/fila")
async def status_fila(canal_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    todos = db.listar_candidatos(canal_id)
    return [v for v in todos if v.status not in [VideoStatus.CANDIDATO, VideoStatus.PUBLICADO]]
```

- [ ] **Step 6: Implementar app/routes/publicacao.py**

```python
# app/routes/publicacao.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.services.publicador import publicar_video
from app.models.video import VideoStatus
import httpx, os

router = APIRouter()

@router.post("/{canal_id}/publicar/{video_id}")
async def publicar(canal_id: str, video_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)

    if not video or video.status != VideoStatus.VIDEO_PRONTO:
        raise HTTPException(400, "Vídeo precisa estar pronto (status: video_pronto)")

    mp4_local = f"temp/{video_id}_final.mp4"
    with httpx.Client(timeout=300) as client:
        r = client.get(video.video_path)
        with open(mp4_local, "wb") as f:
            f.write(r.content)

    thumbnail_local = f"temp/{video_id}_thumbnail.jpg"

    titulo = video.titulo
    descricao = f"Video produced by YT DARK\n\n{' '.join(config.nicho_keywords)}"
    tags = config.nicho_keywords[:10]

    yt_link = publicar_video(mp4_local, titulo, descricao, tags, thumbnail_local)

    video.yt_link = yt_link
    video.status = VideoStatus.PUBLICADO
    db.atualizar_video(canal_id, video)

    for f in [mp4_local, thumbnail_local]:
        if os.path.exists(f):
            os.remove(f)

    return {"video_id": video_id, "yt_link": yt_link, "status": "publicado"}

@router.get("/{canal_id}/publicados")
async def listar_publicados(canal_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    todos = db.listar_candidatos(canal_id)
    return [v for v in todos if v.status == VideoStatus.PUBLICADO]
```

- [ ] **Step 7: Adicionar mutagen ao requirements.txt**

```
mutagen>=1.47.0
```

- [ ] **Step 8: Rodar servidor e checar Swagger**

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Acessa http://localhost:8000/docs — todos os endpoints devem aparecer agrupados por tag.

- [ ] **Step 9: Commit final do backend**

```bash
git add .
git commit -m "feat: pipeline completo (narrador ElevenLabs + editor Shotstack + publicador YouTube)"
git push origin main
```

---

### Task 14: README + Deploy Instructions

**Files:**
- Create: `README.md`

- [ ] **Step 1: Criar README.md**

```markdown
# YT DARK

Sistema de mineração, análise e produção de vídeos para YouTube.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Preencha as keys no .env
uvicorn app.main:app --reload
```

## Uso

Acesse http://localhost:8000/docs para o Swagger UI.

**Fluxo:**
1. `POST /descobrir-canais` — encontra canais por métricas
2. `POST /canais/{id}/minerar` — minera vídeos com score
3. `POST /canais/{id}/aprovar/{video_id}` — aprova candidato
4. `POST /canais/{id}/analisar/{video_id}` — analisa estrutura
5. `POST /canais/{id}/produzir/{video_id}` — gera roteiro + áudio + vídeo
6. `POST /canais/{id}/publicar/{video_id}` — publica no YouTube

## Canais

Cada canal em `canais/{id}/`:
- `config.json` — filtros e configurações
- `channel_dna.json` — identidade visual e editorial
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README com setup e fluxo de uso"
git push origin main
```

---

**Backend completo. Passar para o plano de frontend.**
