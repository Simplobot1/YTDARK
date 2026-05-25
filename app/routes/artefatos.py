"""Serve artefatos do pipeline (audio, thumbnail, video) protegidos por auth."""

import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.auth import verify_token


router = APIRouter()


_TIPOS = {
    "audio": ("narration.mp3", "audio/mpeg"),
    "thumbnail": ("thumbnail.jpg", "image/jpeg"),
    "video": ("final.mp4", "video/mp4"),
    "roteiro": ("roteiro.txt", "text/plain"),
}


@router.get("/artefatos/{canal_id}/{video_id}/{tipo}")
async def servir_artefato(canal_id: str, video_id: str, tipo: str, _=Depends(verify_token)):
    if tipo not in _TIPOS:
        raise HTTPException(400, f"tipo inválido: {tipo}")

    filename, content_type = _TIPOS[tipo]
    path = os.path.join("temp", canal_id, video_id, filename)

    if not os.path.exists(path):
        raise HTTPException(404, f"artefato {tipo} não encontrado")

    return FileResponse(path, media_type=content_type, filename=filename)
