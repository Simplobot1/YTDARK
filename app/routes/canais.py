from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models.canal import CanalConfig, ChannelDNA
from app.services.canal_config import listar_canais, get_config, save_config, get_dna, save_dna
from app.auth import verify_token

router = APIRouter()

class AddFonteRequest(BaseModel):
    handle: str

@router.get("/")
async def get_canais():
    ids = listar_canais()
    canais = []
    for cid in ids:
        try:
            cfg = get_config(cid)
            canais.append({"id": cid, "handle": cfg.youtube_handle, "nicho": cfg.nicho_keywords[:2]})
        except Exception:
            canais.append({"id": cid, "handle": cid, "nicho": []})
    return {"canais": canais}

@router.get("/{canal_id}/fontes")
async def listar_fontes(canal_id: str, _: str = Depends(verify_token)):
    try:
        return {"fontes": get_config(canal_id).canais_fonte}
    except FileNotFoundError:
        raise HTTPException(404, f"Canal '{canal_id}' não encontrado")

@router.post("/{canal_id}/fontes")
async def adicionar_fonte(canal_id: str, body: AddFonteRequest, _: str = Depends(verify_token)):
    try:
        config = get_config(canal_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Canal '{canal_id}' não encontrado")
    handle = body.handle if body.handle.startswith("@") else f"@{body.handle}"
    if handle not in config.canais_fonte:
        config.canais_fonte.append(handle)
        save_config(canal_id, config)
    return {"ok": True, "fontes": config.canais_fonte}

@router.delete("/{canal_id}/fontes/{handle}")
async def remover_fonte(canal_id: str, handle: str, _: str = Depends(verify_token)):
    try:
        config = get_config(canal_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Canal '{canal_id}' não encontrado")
    norm = handle if handle.startswith("@") else f"@{handle}"
    config.canais_fonte = [f for f in config.canais_fonte if f != norm]
    save_config(canal_id, config)
    return {"ok": True, "fontes": config.canais_fonte}

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
