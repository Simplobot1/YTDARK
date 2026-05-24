import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.services.publicador import publicar_video
from app.models.video import VideoStatus

router = APIRouter()


@router.post("/{canal_id}/publicar/{video_id}")
async def publicar(canal_id: str, video_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)

    if not video or video.status != VideoStatus.VIDEO_PRONTO:
        raise HTTPException(400, "Vídeo precisa estar pronto (status: video_pronto)")

    os.makedirs("temp", exist_ok=True)
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

    for fp in [mp4_local, thumbnail_local]:
        if os.path.exists(fp):
            os.remove(fp)

    return {"video_id": video_id, "yt_link": yt_link, "status": "publicado"}


@router.get("/{canal_id}/publicados")
async def listar_publicados(canal_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    todos = db.listar_candidatos(canal_id)
    return [v for v in todos if v.status == VideoStatus.PUBLICADO]
