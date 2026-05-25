from typing import List, Optional
from datetime import date
from functools import lru_cache
from supabase import create_client, Client
from app.services.db import DatabaseInterface
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings


@lru_cache()
def _client() -> Client:
    s = get_settings()
    key = s.supabase_service_role_key or s.supabase_anon_key
    return create_client(s.supabase_url, key)


def _video_to_row(canal_id: str, video: Video) -> dict:
    d = video.model_dump()
    d["canal_id"] = canal_id
    d["status"] = video.status.value
    return d


def _row_to_video(r: dict) -> Video:
    r = {k: v for k, v in r.items() if k not in ("id", "canal_id", "created_at")}
    r["status"] = VideoStatus(r.get("status", "candidato"))
    return Video(**r)


class SupabaseDatabase(DatabaseInterface):

    def salvar_video(self, canal_id: str, video: Video) -> None:
        _client().table("videos").upsert(
            _video_to_row(canal_id, video), on_conflict="canal_id,video_id"
        ).execute()

    def listar_candidatos(self, canal_id: str) -> List[Video]:
        resp = _client().table("videos").select("*").eq("canal_id", canal_id).execute()
        result = []
        for r in resp.data or []:
            try:
                result.append(_row_to_video(r))
            except Exception:
                continue
        return result

    def atualizar_status(self, canal_id: str, video_id: str, status: VideoStatus) -> None:
        _client().table("videos").update({"status": status.value}).eq(
            "canal_id", canal_id
        ).eq("video_id", video_id).execute()

    def atualizar_video(self, canal_id: str, video: Video) -> None:
        row = _video_to_row(canal_id, video)
        row.pop("canal_id", None)
        _client().table("videos").update(row).eq("canal_id", canal_id).eq(
            "video_id", video.video_id
        ).execute()

    def buscar_video(self, canal_id: str, video_id: str) -> Optional[Video]:
        resp = (
            _client().table("videos").select("*")
            .eq("canal_id", canal_id)
            .eq("video_id", video_id)
            .execute()
        )
        if resp.data:
            try:
                return _row_to_video(resp.data[0])
            except Exception:
                pass
        return None

    def salvar_candidato_canal(self, canal_id: str, candidato: CanalCandidato) -> None:
        row = {
            "canal_id": canal_id,
            "handle": candidato.handle,
            "nome": candidato.nome,
            "channel_id": candidato.channel_id,
            "subscribers": candidato.metricas.subscribers,
            "avg_views": candidato.metricas.avg_views,
            "engagement_rate": candidato.metricas.engagement_rate,
            "upload_freq_mensal": candidato.metricas.upload_freq_mensal,
            "avg_duration_min": candidato.metricas.avg_duration_min,
            "momentum": candidato.metricas.momentum,
            "score": candidato.score,
            "melhor_video_recente": candidato.melhor_video_recente,
            "adicionado": candidato.adicionado,
        }
        _client().table("canais_candidatos").upsert(
            row, on_conflict="canal_id,handle"
        ).execute()

    def listar_candidatos_canal(self, canal_id: str) -> List[CanalCandidato]:
        resp = (
            _client().table("canais_candidatos").select("*")
            .eq("canal_id", canal_id)
            .execute()
        )
        result = []
        for r in resp.data or []:
            try:
                result.append(CanalCandidato(
                    handle=r["handle"],
                    nome=r["nome"],
                    channel_id=r["channel_id"],
                    metricas=MetricasCanal(
                        subscribers=r["subscribers"],
                        avg_views=r["avg_views"],
                        engagement_rate=r["engagement_rate"],
                        upload_freq_mensal=r["upload_freq_mensal"],
                        avg_duration_min=r["avg_duration_min"],
                        momentum=r["momentum"],
                    ),
                    score=r["score"],
                    melhor_video_recente=r.get("melhor_video_recente"),
                    adicionado=r.get("adicionado", False),
                ))
            except Exception:
                continue
        return result

    def salvar_keyword(self, canal_id: str, termo: str, volume: int, competition: float, seo_score: float) -> None:
        _client().table("keywords").upsert(
            {
                "canal_id": canal_id,
                "termo": termo,
                "volume": volume,
                "competition": competition,
                "seo_score": seo_score,
                "data": str(date.today()),
            },
            on_conflict="canal_id,termo",
        ).execute()
