from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes import auth, descoberta, mineracao, analise, producao, publicacao, canais

load_dotenv()

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
