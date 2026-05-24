from pydantic import BaseModel
from typing import List

class FiltrosMineracao(BaseModel):
    min_views: int = 50000
    max_dias: int = 30
    duracao_min_min: float = 8.0
    duracao_max_min: float = 20.0
    sem_legenda_pt: bool = True

class CanalConfig(BaseModel):
    canal_id: str
    youtube_handle: str
    idioma: str = "en"
    nicho_keywords: List[str] = []
    canais_fonte: List[str] = []
    tipo_video_padrao: str = "whiteboard"
    tipos_video_suportados: List[str] = ["whiteboard", "talking_head"]
    elevenlabs_voice_id: str = ""
    google_sheets_id: str = ""
    google_drive_folder_id: str = ""
    filtros_mineracao: FiltrosMineracao = FiltrosMineracao()

class ChannelDNA(BaseModel):
    estilo_visual: str = "whiteboard"
    tom_voz: str = "casual and educational"
    paleta_cores: List[str] = ["#FF6B35", "#FFFFFF", "#2C3E50"]
    intro_max_sec: int = 30
    hook_style: str = "bold question or shocking stat"
    num_pontos: int = 5
    cta_style: str = "subscribe + next video suggestion"
    thumbnail_formula: str = "bold text left + visual right"
    thumbnail_fonte: str = "Montserrat Bold"
    titulo_formula: str = "[Number] Ways to [Benefit] (No [Common Excuse])"
    duracao_alvo_min: int = 12
