from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.auth import verify_token
from app.services.channel_discovery import discover_channels
from app.services.supabase_db import SupabaseDatabase
from app.models.canal_candidato import CanalCandidato

router = APIRouter()


class FiltrosDescoberta(BaseModel):
    subscribers_min: int = 100000
    subscribers_max: int = 3000000
    avg_views_min: int = 50000
    upload_freq_min: int = 2
    avg_duration_min_min: float = 0
    avg_duration_max_min: float = 60


class DescobertaRequest(BaseModel):
    nicho: str = "personal finance"
    seed_channel: Optional[str] = None
    idioma: str = "en"
    periodo_dias: int = 90
    ordem: str = "viewCount"
    filtros: FiltrosDescoberta = FiltrosDescoberta()
    top_n: int = 20


@router.post("/descobrir-canais", response_model=List[CanalCandidato])
async def descobrir_canais(body: DescobertaRequest, _: str = Depends(verify_token)):
    try:
        return discover_channels(
            nicho=body.nicho,
            seed_channel=body.seed_channel,
            idioma=body.idioma,
            periodo_dias=body.periodo_dias,
            ordem=body.ordem,
            filtros=body.filtros.model_dump(),
            top_n=body.top_n,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_db() -> SupabaseDatabase:
    return SupabaseDatabase()


class SalvarCanaisRequest(BaseModel):
    canais: List[CanalCandidato]


@router.post("/descobrir-canais/salvar/{canal_id}")
async def salvar_canais_descobertos(
    canal_id: str,
    body: SalvarCanaisRequest,
    _: str = Depends(verify_token),
):
    db = _get_db()
    for c in body.canais:
        db.salvar_candidato_canal(canal_id, c)
    return {"salvos": len(body.canais)}


@router.get("/descobrir-canais/salvos/{canal_id}", response_model=List[CanalCandidato])
async def listar_canais_salvos(canal_id: str, _: str = Depends(verify_token)):
    return _get_db().listar_candidatos_canal(canal_id)
