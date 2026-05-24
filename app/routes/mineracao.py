from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.minerador import minerar_canal
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.models.video import VideoStatus

router = APIRouter()

def _get_db(canal_id: str) -> SheetsDatabase:
    config = get_config(canal_id)
    if not config.google_sheets_id:
        raise HTTPException(400, "google_sheets_id não configurado para este canal")
    return SheetsDatabase(config.google_sheets_id)

@router.post("/{canal_id}/minerar")
async def minerar(canal_id: str, _: str = Depends(verify_token)):
    config = get_config(canal_id)
    videos = minerar_canal(config)
    if config.google_sheets_id:
        db = _get_db(canal_id)
        for v in videos:
            db.salvar_video(canal_id, v)
    return {"minerados": len(videos), "videos": [v.model_dump() for v in videos]}

@router.get("/{canal_id}/candidatos")
async def listar_candidatos(canal_id: str, _: str = Depends(verify_token)):
    db = _get_db(canal_id)
    return db.listar_candidatos(canal_id)

@router.post("/{canal_id}/aprovar/{video_id}")
async def aprovar_video(canal_id: str, video_id: str, _: str = Depends(verify_token)):
    db = _get_db(canal_id)
    db.atualizar_status(canal_id, video_id, VideoStatus.APROVADO)
    return {"ok": True, "video_id": video_id, "status": "aprovado"}
