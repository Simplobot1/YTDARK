"""Montagem de vídeo via FFmpeg: thumbnail estática + narração (+ bg music opcional)."""

import os
import logging
import subprocess
from typing import Optional


log = logging.getLogger("ytdark.video_editor")


def montar_video(
    thumbnail_path: str,
    audio_path: str,
    video_id: str,
    canal_id: str,
    bg_music_path: Optional[str] = None,
    vol_narracao: float = 1.0,
    vol_musica: float = 0.05,
) -> str:
    """Monta MP4 com FFmpeg.

    Strategy: imagem em loop como vídeo (1920x1080), narração mixada com música
    de fundo opcional. Duração: igual ao áudio (shortest).

    Returns:
        Path absoluto do MP4 gerado.

    Raises:
        RuntimeError: Se FFmpeg falhar.
        FileNotFoundError: Se ffmpeg não estiver no PATH.
    """
    out_dir = os.path.join("temp", canal_id, video_id)
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, "final.mp4")

    if bg_music_path and os.path.exists(bg_music_path):
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", thumbnail_path,
            "-i", audio_path,
            "-stream_loop", "-1", "-i", bg_music_path,
            "-filter_complex",
            (
                f"[1:a]volume={vol_narracao}[a1];"
                f"[2:a]volume={vol_musica}[a2];"
                f"[a1][a2]amix=inputs=2:duration=first[aout]"
            ),
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
            "-shortest",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", thumbnail_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
            "-shortest",
            output_path,
        ]

    log.info("FFmpeg cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

    if result.returncode != 0:
        tail = (result.stderr or "")[-500:]
        raise RuntimeError(f"ffmpeg_failed: {tail}")

    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Retorna duração em segundos. Fallback: 600s se ffprobe falhar."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return 600.0
