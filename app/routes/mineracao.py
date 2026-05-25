from fastapi import APIRouter, Depends, Query
from app.auth import verify_token
from app.services.minerador import minerar_canal
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.services.file_db import FileDatabase
from app.models.video import VideoStatus
from app.config import get_settings

router = APIRouter()

_FILA_STATUS = {
    VideoStatus.APROVADO, VideoStatus.ANALISADO,
    VideoStatus.ROTEIRO_GERADO, VideoStatus.AUDIO_GERADO, VideoStatus.VIDEO_PRONTO,
}

def _get_db(canal_id: str):
    s = get_settings()
    if s.supabase_url and (s.supabase_service_role_key or s.supabase_anon_key):
        from app.services.supabase_db import SupabaseDatabase
        return SupabaseDatabase()
    config = get_config(canal_id)
    if config.google_sheets_id:
        return SheetsDatabase(config.google_sheets_id)
    return FileDatabase()

@router.post("/{canal_id}/minerar")
async def minerar(canal_id: str, _: str = Depends(verify_token)):
    config = get_config(canal_id)
    videos = minerar_canal(config)
    db = _get_db(canal_id)
    for v in videos:
        db.salvar_video(canal_id, v)
    return {"minerados": len(videos), "videos": [v.model_dump() for v in videos]}

@router.get("/{canal_id}/candidatos")
async def listar_candidatos(
    canal_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(verify_token),
):
    db = _get_db(canal_id)
    todos = [v for v in db.listar_candidatos(canal_id) if v.status == VideoStatus.CANDIDATO]
    total = len(todos)
    start = (page - 1) * limit
    pagina = todos[start : start + limit]
    return {
        "videos": [v.model_dump() for v in pagina],
        "total": total,
        "page": page,
        "pages": -(-total // limit),
    }

@router.get("/{canal_id}/fila")
async def listar_fila(canal_id: str, _: str = Depends(verify_token)):
    db = _get_db(canal_id)
    todos = db.listar_candidatos(canal_id)
    return [v.model_dump() for v in todos if v.status in _FILA_STATUS]

@router.get("/{canal_id}/publicados")
async def listar_publicados(canal_id: str, _: str = Depends(verify_token)):
    db = _get_db(canal_id)
    todos = db.listar_candidatos(canal_id)
    return [v.model_dump() for v in todos if v.status == VideoStatus.PUBLICADO]

@router.post("/{canal_id}/aprovar/{video_id}")
async def aprovar_video(canal_id: str, video_id: str, _: str = Depends(verify_token)):
    db = _get_db(canal_id)
    db.atualizar_status(canal_id, video_id, VideoStatus.APROVADO)
    return {"ok": True, "video_id": video_id, "status": "aprovado"}
