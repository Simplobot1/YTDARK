from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes import auth, descoberta, mineracao, canais, remodelacao, artefatos

load_dotenv()

app = FastAPI(
    title="YT DARK API",
    description="Sistema de mineração, análise e remodelação de vídeos",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ytdark.pages.dev", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(descoberta.router, tags=["Descoberta"])
app.include_router(mineracao.router, prefix="/canais", tags=["Mineração"])
app.include_router(canais.router, prefix="/canais", tags=["Canais"])
app.include_router(remodelacao.router, prefix="/canais", tags=["Remodelação"])
app.include_router(artefatos.router, tags=["Artefatos"])


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "2.0.0"}
