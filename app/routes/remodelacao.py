"""Pipeline de remodelação de vídeos — 7 etapas, cada uma com endpoint próprio."""

import os
import json
import asyncio
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import verify_token
from app.config import get_settings
from app.services.canal_config import get_config
from app.services.supabase_db import SupabaseDatabase
from app.services.transcritor import transcrever
from app.services.analisador import analisar_video
from app.services.roteirista import gerar_roteiro, gerar_titulo, gerar_seo
from app.services.narrador import gerar_narracao
from app.services.thumbnail_gen import gerar_thumbnail, construir_prompt_thumbnail
from app.services.video_editor import montar_video, get_audio_duration
from app.services.publicador import publicar_video
from app.models.video import VideoStatus


router = APIRouter()
log = logging.getLogger("ytdark.remodelacao")


def _db() -> SupabaseDatabase:
    return SupabaseDatabase()


def _get_video_or_404(db: SupabaseDatabase, canal_id: str, video_id: str):
    video = db.buscar_video(canal_id, video_id)
    if not video:
        raise HTTPException(404, f"video {video_id} não encontrado")
    return video


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _audio_path(canal_id: str, video_id: str) -> str:
    return os.path.join("temp", canal_id, video_id, "narration.mp3")


def _thumb_path(canal_id: str, video_id: str) -> str:
    return os.path.join("temp", canal_id, video_id, "thumbnail.jpg")


def _video_path(canal_id: str, video_id: str) -> str:
    return os.path.join("temp", canal_id, video_id, "final.mp4")


# ─── Status ───────────────────────────────────────────────────────────────────

@router.get("/{canal_id}/remodelar/{video_id}/status")
async def status_pipeline(canal_id: str, video_id: str, _=Depends(verify_token)):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)
    status_val = video.status.value if hasattr(video.status, "value") else str(video.status)
    return {
        "video_id": video_id,
        "status": status_val,
        "titulo": video.titulo,
        "tem_transcricao": bool(video.transcricao),
        "tem_analise": bool(video.prompt_titulo),
        "tem_roteiro": bool(video.roteiro),
        "tem_audio": bool(video.audio_path),
        "tem_thumbnail": bool(video.thumbnail_path),
        "tem_video": bool(video.video_path),
        "tem_yt_link": bool(video.yt_link),
    }


# ─── 1. Transcrever ───────────────────────────────────────────────────────────

class TranscreverRequest(BaseModel):
    force: bool = False
    languages: List[str] = ["en", "pt", "es"]


@router.post("/{canal_id}/remodelar/{video_id}/transcrever")
async def transcrever_video(
    canal_id: str, video_id: str, body: TranscreverRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    if video.transcricao and not body.force:
        return {
            "video_id": video_id,
            "transcricao": video.transcricao,
            "char_count": len(video.transcricao),
            "cached": True,
        }

    try:
        transcricao = transcrever(video_id, body.languages)
    except ValueError as e:
        raise HTTPException(422, str(e))

    db.atualizar_campos(canal_id, video_id, transcricao=transcricao)
    return {
        "video_id": video_id,
        "transcricao": transcricao,
        "char_count": len(transcricao),
        "cached": False,
    }


# ─── 2. Analisar ──────────────────────────────────────────────────────────────

class AnalisarRequest(BaseModel):
    force: bool = False


@router.post("/{canal_id}/remodelar/{video_id}/analisar")
async def analisar(
    canal_id: str, video_id: str, body: AnalisarRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    if video.prompt_titulo and not body.force:
        return {
            "video_id": video_id,
            "prompt_titulo": video.prompt_titulo,
            "estrutura_video": video.estrutura_video,
            "estrutura_thumb": video.estrutura_thumb,
            "cached": True,
        }

    if not video.transcricao:
        raise HTTPException(422, "Transcreva o vídeo primeiro")

    resultado = analisar_video(video.titulo, video.transcricao, video_id)
    db.atualizar_campos(
        canal_id, video_id,
        prompt_titulo=resultado["prompt_titulo"],
        estrutura_video=resultado["estrutura_video"],
        estrutura_thumb=resultado["estrutura_thumb"],
        status=VideoStatus.ANALISADO.value,
    )
    return {**resultado, "video_id": video_id, "cached": False}


# ─── 3. Roteirizar (SSE) ──────────────────────────────────────────────────────

class RoteirizarRequest(BaseModel):
    idioma: str = "en"
    force: bool = False
    titulo_novo: Optional[str] = None


@router.post("/{canal_id}/remodelar/{video_id}/roteirizar")
async def roteirizar(
    canal_id: str, video_id: str, body: RoteirizarRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    if video.roteiro and not body.force:
        async def cached_stream():
            yield _sse_event(
                "done",
                {
                    "roteiro": video.roteiro,
                    "char_count": len(video.roteiro),
                    "titulo": video.titulo,
                    "cached": True,
                },
            )

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # Gera novo título ou reutiliza original
    titulo_alvo = body.titulo_novo or (
        gerar_titulo(video.prompt_titulo, body.idioma) if video.prompt_titulo else video.titulo
    )

    async def stream():
        try:
            yield _sse_event("progress", {"step": "gerando_titulo", "titulo": titulo_alvo})
            await asyncio.sleep(0)

            yield _sse_event("progress", {"step": "parte_1"})
            await asyncio.sleep(0)

            loop = asyncio.get_event_loop()
            roteiro = await loop.run_in_executor(
                None,
                lambda: gerar_roteiro(
                    titulo=titulo_alvo,
                    idioma=body.idioma,
                    transcricao_ref=video.transcricao or "",
                    estrutura_ref=video.estrutura_video or "",
                ),
            )

            db.atualizar_campos(
                canal_id, video_id,
                roteiro=roteiro,
                status=VideoStatus.ROTEIRO_GERADO.value,
            )
            yield _sse_event(
                "done",
                {
                    "roteiro": roteiro,
                    "char_count": len(roteiro),
                    "titulo": titulo_alvo,
                    "cached": False,
                },
            )
        except Exception as e:
            log.exception("erro_roteiro")
            yield _sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── 4. Narrar ────────────────────────────────────────────────────────────────

class NarrarRequest(BaseModel):
    voice_id: Optional[str] = None
    force: bool = False


@router.post("/{canal_id}/remodelar/{video_id}/narrar")
async def narrar(
    canal_id: str, video_id: str, body: NarrarRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    audio_local = _audio_path(canal_id, video_id)
    if video.audio_path and os.path.exists(audio_local) and not body.force:
        return {
            "video_id": video_id,
            "audio_path": audio_local,
            "audio_url": f"/artefatos/{canal_id}/{video_id}/audio",
            "cached": True,
        }

    if not video.roteiro:
        raise HTTPException(422, "Gere o roteiro primeiro")

    os.makedirs(os.path.dirname(audio_local), exist_ok=True)

    # narrador.gerar_narracao gera em temp/{video_id}.mp3
    # Passamos subpath para que vá direto ao diretório correto
    gerado = gerar_narracao(
        video.roteiro,
        f"{canal_id}/{video_id}/narration",
        body.voice_id,
    )
    duracao = get_audio_duration(gerado)
    size = os.path.getsize(gerado) if os.path.exists(gerado) else 0

    db.atualizar_campos(
        canal_id, video_id,
        audio_path=gerado,
        status=VideoStatus.AUDIO_GERADO.value,
    )
    return {
        "video_id": video_id,
        "audio_path": gerado,
        "audio_url": f"/artefatos/{canal_id}/{video_id}/audio",
        "duracao_sec": duracao,
        "size_bytes": size,
        "cached": False,
    }


# ─── 5. Thumbnail ─────────────────────────────────────────────────────────────

class ThumbnailRequest(BaseModel):
    image_provider: str = "together"
    prompt_extra: str = ""
    force: bool = False


@router.post("/{canal_id}/remodelar/{video_id}/thumbnail")
async def thumbnail(
    canal_id: str, video_id: str, body: ThumbnailRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    thumb_local = _thumb_path(canal_id, video_id)
    if video.thumbnail_path and os.path.exists(thumb_local) and not body.force:
        return {
            "video_id": video_id,
            "thumbnail_path": thumb_local,
            "thumbnail_url": f"/artefatos/{canal_id}/{video_id}/thumbnail",
            "provider_used": body.image_provider,
            "cached": True,
        }

    prompt = construir_prompt_thumbnail(video.estrutura_thumb or "", video.titulo)
    if body.prompt_extra:
        prompt += f" {body.prompt_extra}"

    try:
        local = gerar_thumbnail(prompt, video_id, canal_id, body.image_provider)
    except Exception as e:
        log.exception("erro_thumbnail")
        raise HTTPException(500, f"thumbnail_failed: {e}")

    db.atualizar_campos(canal_id, video_id, thumbnail_path=local)
    return {
        "video_id": video_id,
        "thumbnail_path": local,
        "thumbnail_url": f"/artefatos/{canal_id}/{video_id}/thumbnail",
        "provider_used": body.image_provider,
        "prompt_final": prompt[:200],
        "cached": False,
    }


# ─── 6. Montar vídeo (SSE) ────────────────────────────────────────────────────

class MontarRequest(BaseModel):
    bg_music_path: Optional[str] = None
    vol_narracao: float = 1.0
    vol_musica: float = 0.05
    force: bool = False


@router.post("/{canal_id}/remodelar/{video_id}/montar")
async def montar(
    canal_id: str, video_id: str, body: MontarRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)

    final_local = _video_path(canal_id, video_id)
    audio_local = _audio_path(canal_id, video_id)
    thumb_local = _thumb_path(canal_id, video_id)

    if video.video_path and os.path.exists(final_local) and not body.force:
        async def cached_stream():
            yield _sse_event(
                "done",
                {
                    "video_path": final_local,
                    "video_url": f"/artefatos/{canal_id}/{video_id}/video",
                    "cached": True,
                },
            )

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    if not os.path.exists(audio_local):
        raise HTTPException(422, "Gere a narração primeiro")
    if not os.path.exists(thumb_local):
        raise HTTPException(422, "Gere a thumbnail primeiro")

    settings = get_settings()
    bg = body.bg_music_path or settings.bg_music_path

    async def stream():
        try:
            yield _sse_event("progress", {"step": "iniciando_ffmpeg"})
            await asyncio.sleep(0)

            loop = asyncio.get_event_loop()
            out = await loop.run_in_executor(
                None,
                lambda: montar_video(
                    thumbnail_path=thumb_local,
                    audio_path=audio_local,
                    video_id=video_id,
                    canal_id=canal_id,
                    bg_music_path=bg if (bg and os.path.exists(bg)) else None,
                    vol_narracao=body.vol_narracao,
                    vol_musica=body.vol_musica,
                ),
            )

            size = os.path.getsize(out)
            db.atualizar_campos(
                canal_id, video_id,
                video_path=out,
                status=VideoStatus.VIDEO_PRONTO.value,
            )
            yield _sse_event(
                "done",
                {
                    "video_path": out,
                    "video_url": f"/artefatos/{canal_id}/{video_id}/video",
                    "size_bytes": size,
                    "cached": False,
                },
            )
        except Exception as e:
            log.exception("erro_montagem")
            yield _sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── SEO ──────────────────────────────────────────────────────────────────────

class SeoRequest(BaseModel):
    idioma: str = "en"


@router.post("/{canal_id}/remodelar/{video_id}/gerar-seo")
async def gerar_seo_endpoint(
    canal_id: str, video_id: str, body: SeoRequest, _=Depends(verify_token)
):
    db = _db()
    video = _get_video_or_404(db, canal_id, video_id)
    config = get_config(canal_id)

    if not video.roteiro:
        raise HTTPException(422, "Gere o roteiro primeiro")

    seo = gerar_seo(video.titulo, video.roteiro, body.idioma, config.nicho_keywords)
    return {**seo, "video_id": video_id}


# ─── 7. Publicar ──────────────────────────────────────────────────────────────

class PublicarRequest(BaseModel):
    titulo: str
    descricao: str
    tags: List[str] = []
    privacy: str = "private"


@router.post("/{canal_id}/remodelar/{video_id}/publicar")
async def publicar(
    canal_id: str, video_id: str, body: PublicarRequest, _=Depends(verify_token)
):
    db = _db()
    _get_video_or_404(db, canal_id, video_id)

    final_local = _video_path(canal_id, video_id)
    thumb_local = _thumb_path(canal_id, video_id)

    if not os.path.exists(final_local):
        raise HTTPException(422, "Monte o vídeo primeiro")

    thumb = thumb_local if os.path.exists(thumb_local) else ""

    try:
        yt_link = publicar_video(final_local, body.titulo, body.descricao, body.tags, thumb)
    except Exception as e:
        log.exception("erro_publicacao")
        raise HTTPException(500, f"publicacao_failed: {e}")

    db.atualizar_campos(
        canal_id, video_id,
        yt_link=yt_link,
        descricao_seo=body.descricao,
        tags_seo=body.tags,
        status=VideoStatus.PUBLICADO.value,
    )
    return {"video_id": video_id, "yt_link": yt_link, "status": "publicado"}
