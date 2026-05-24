from pydantic import BaseModel
from enum import Enum
from typing import Optional

class VideoStatus(str, Enum):
    CANDIDATO = "candidato"
    APROVADO = "aprovado"
    MINERADO = "minerado"
    ANALISADO = "analisado"
    ROTEIRO_GERADO = "roteiro_gerado"
    AUDIO_GERADO = "audio_gerado"
    VIDEO_PRONTO = "video_pronto"
    PUBLICADO = "publicado"

class Video(BaseModel):
    video_id: str
    titulo: str
    canal_fonte: str
    views: int
    data_pub: str
    duracao_min: float
    tipo: str = "whiteboard"
    score: float = 0.0
    status: VideoStatus = VideoStatus.CANDIDATO
    transcricao: Optional[str] = None
    analise: Optional[dict] = None
    roteiro_path: Optional[str] = None
    audio_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    video_path: Optional[str] = None
    drive_link: Optional[str] = None
    yt_link: Optional[str] = None
