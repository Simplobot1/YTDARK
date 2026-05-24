import os
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

router = APIRouter()


def _maybe_upload(local_path: str, folder_id: str, mime_type: str) -> str:
    """Faz upload pro Drive se o folder_id estiver configurado; senão devolve o caminho local."""
    if folder_id:
        return upload_file(local_path, folder_id, mime_type)
    return local_path


@router.post("/{canal_id}/produzir/{video_id}")
async def produzir_video(canal_id: str, video_id: str, _=Depends(verify_token)):
    config = get_config(canal_id)
    dna = get_dna(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)

    if not video or not video.analise:
        raise HTTPException(400, "Vídeo precisa estar analisado antes de produzir")

    # 1. Roteiro
    roteiro = gerar_roteiro(video.analise, dna, config)
    roteiro_path = f"temp/{video_id}_roteiro.txt"
    os.makedirs("temp", exist_ok=True)
    with open(roteiro_path, "w", encoding="utf-8") as f:
        f.write(roteiro)
    roteiro_drive = _maybe_upload(roteiro_path, config.google_drive_folder_id, "text/plain")
    video.status = VideoStatus.ROTEIRO_GERADO

    # 2. Thumbnail
    titulo_video = roteiro.split("\n")[0].replace("[TÍTULO]", "").strip() or video.titulo
    thumbnail_local = gerar_thumbnail(titulo_video, dna, video_id)
    thumbnail_drive = _maybe_upload(thumbnail_local, config.google_drive_folder_id, "image/jpeg")

    # 3. Áudio
    audio_local = gerar_narracao(roteiro, video_id)
    audio_drive = _maybe_upload(audio_local, config.google_drive_folder_id, "audio/mpeg")
    video.status = VideoStatus.AUDIO_GERADO

    # 4. Duração do áudio
    try:
        from mutagen.mp3 import MP3
        duracao_sec = MP3(audio_local).info.length
    except Exception:
        duracao_sec = 600.0

    # 5. Montagem do vídeo (Shotstack)
    mp4_url = montar_video(
        tipo_template=video.analise.get("tipo_video", config.tipo_video_padrao),
        audio_url=audio_drive,
        thumbnail_url=thumbnail_drive,
        titulo=titulo_video,
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
