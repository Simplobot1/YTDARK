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
