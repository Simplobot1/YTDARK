"""Transcrição via YouTube Transcript API (sem download de áudio)."""

from typing import List, Optional


def transcrever(video_id: str, idiomas: Optional[List[str]] = None) -> str:
    """Busca transcrição diretamente do YouTube.

    Args:
        video_id: ID do vídeo do YouTube.
        idiomas: Lista de códigos de idioma em ordem de preferência. Default: ["en", "pt", "es"].

    Returns:
        Texto da transcrição, concatenado.

    Raises:
        ValueError: Se nenhuma transcrição estiver disponível ou ocorrer erro de rede.
    """
    if idiomas is None:
        idiomas = ["en", "pt", "es"]

    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi,
            NoTranscriptFound,
            TranscriptsDisabled,
        )
    except ImportError as e:
        raise ValueError(f"youtube_transcript_api não instalado: {e}")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 1) Tenta cada idioma preferido (manual ou gerado)
        for lang in idiomas:
            try:
                t = transcript_list.find_transcript([lang])
                entries = t.fetch()
                return " ".join(e["text"] for e in entries if e.get("text")).strip()
            except Exception:
                continue

        # 2) Fallback: qualquer transcrição gerada disponível
        try:
            for t in transcript_list:
                entries = t.fetch()
                texto = " ".join(e["text"] for e in entries if e.get("text")).strip()
                if texto:
                    return texto
        except Exception:
            pass

        raise ValueError(f"no_transcript_available: nenhuma transcrição encontrada para {video_id}")

    except (NoTranscriptFound, TranscriptsDisabled) as e:
        raise ValueError(f"no_transcript_available: {str(e)}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"transcript_error: {str(e)}")
