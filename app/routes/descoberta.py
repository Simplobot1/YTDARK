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
async def descobrir_canais(body: DescobertaRequest, _: str = Depends(verify_token)):
    return discover_channels(
        estrategia=body.estrategia,
        nicho=body.nicho,
        idioma=body.idioma,
        filtros=body.filtros,
        top_n=body.top_n,
        seed_channel=body.seed_channel,
    )
