from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.services.scraper import extract_frames, download_audio, cleanup_temp
from app.services.transcritor import transcrever
from app.services.analisador import analisar_frames
from app.services.drive import upload_file
from app.services.canal_config import get_config
from app.services.sheets_impl import SheetsDatabase
from app.models.video import VideoStatus

router = APIRouter()


@router.post("/{canal_id}/analisar/{video_id}")
async def analisar_video(canal_id: str, video_id: str, _: str = Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    video = db.buscar_video(canal_id, video_id)
    if not video:
        raise HTTPException(404, f"Video {video_id} não encontrado")

    audio_path = download_audio(video_id)
    transcricao = transcrever(audio_path, config.idioma)
    frames = extract_frames(video_id)
    analise = analisar_frames(frames, transcricao, video.titulo)

    if config.google_drive_folder_id:
        for frame in frames:
            upload_file(frame, config.google_drive_folder_id, "image/jpeg")

    video.transcricao = transcricao
    video.analise = analise
    video.status = VideoStatus.ANALISADO
    db.atualizar_video(canal_id, video)
    cleanup_temp(video_id)

    return {
        "video_id": video_id,
        "analise": analise,
        "transcricao_preview": transcricao[:200],
    }


@router.get("/{canal_id}/analisados")
async def listar_analisados(canal_id: str, _: str = Depends(verify_token)):
    config = get_config(canal_id)
    db = SheetsDatabase(config.google_sheets_id)
    todos = db.listar_candidatos(canal_id)
    return [v for v in todos if v.status == VideoStatus.ANALISADO]
