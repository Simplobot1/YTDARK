from pydantic import BaseModel
from typing import Optional

class MetricasCanal(BaseModel):
    subscribers: int
    avg_views: float
    engagement_rate: float
    upload_freq_mensal: float
    avg_duration_min: float
    momentum: str

class CanalCandidato(BaseModel):
    handle: str
    nome: str
    channel_id: str
    metricas: MetricasCanal
    score: float
    melhor_video_recente: Optional[dict] = None
    adicionado: bool = False
