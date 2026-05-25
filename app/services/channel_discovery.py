from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import HTTPException
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings

def _get_yt_service():
    return build("youtube", "v3", developerKey=get_settings().youtube_api_key)

def _calc_score(subs: int, avg_views: float) -> float:
    norm_views = min(avg_views / 500000, 1.0) * 60
    norm_subs = min(subs / 1000000, 1.0) * 40
    return round(norm_views + norm_subs, 2)

def _resolve_channel_by_handle(service, handle: str) -> Optional[dict]:
    """Resolve canal pelo handle usando channels.list (1 unidade de quota)."""
    clean = handle.lstrip("@")
    try:
        resp = service.channels().list(
            part="snippet,statistics",
            forHandle=clean,
        ).execute()
        items = resp.get("items", [])
        if items:
            return items[0]
    except HttpError:
        pass
    return None

def _search_channels(service, query: str, idioma: str, max_results: int) -> List[str]:
    """Busca IDs de canais por query (100 unidades de quota por chamada)."""
    resp = service.search().list(
        part="snippet",
        q=query,
        type="channel",
        relevanceLanguage=idioma or "en",
        maxResults=min(max_results, 50),
    ).execute()
    return [i["snippet"]["channelId"] for i in resp.get("items", [])]

def _get_channels_stats(service, channel_ids: List[str]) -> List[dict]:
    """Pega estatísticas de múltiplos canais de uma vez (1 unidade de quota)."""
    if not channel_ids:
        return []
    resp = service.channels().list(
        part="snippet,statistics",
        id=",".join(channel_ids[:50]),
    ).execute()
    return resp.get("items", [])

def _build_candidato(item: dict, filtros: dict) -> Optional[CanalCandidato]:
    try:
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        subs = int(stats.get("subscriberCount", 0))
        total_views = int(stats.get("viewCount", 0))
        video_count = max(int(stats.get("videoCount", 1)), 1)
        avg_views = total_views / video_count

        if subs < filtros.get("subscribers_min", 0): return None
        if subs > filtros.get("subscribers_max", 999_999_999): return None
        if avg_views < filtros.get("avg_views_min", 0): return None

        handle = snippet.get("customUrl", "")
        if not handle:
            handle = snippet.get("title", item["id"]).replace(" ", "")
        if not handle.startswith("@"):
            handle = f"@{handle}"

        return CanalCandidato(
            handle=handle,
            nome=snippet.get("title", item["id"]),
            channel_id=item["id"],
            metricas=MetricasCanal(
                subscribers=subs,
                avg_views=round(avg_views, 0),
                engagement_rate=0.0,
                upload_freq_mensal=0,
                avg_duration_min=0.0,
                momentum="estavel",
            ),
            score=_calc_score(subs, avg_views),
        )
    except Exception:
        return None

def discover_channels(
    nicho: str,
    idioma: str,
    filtros: dict,
    top_n: int = 20,
    seed_channel: Optional[str] = None,
    periodo_dias: int = 90,
    ordem: str = "viewCount",
) -> List[CanalCandidato]:
    try:
        service = _get_yt_service()
    except Exception as e:
        raise HTTPException(500, f"Erro ao conectar ao YouTube API: {e}")

    channel_ids: set = set()

    # Busca por nicho (100 unidades)
    if nicho.strip():
        try:
            ids = _search_channels(service, nicho.strip(), idioma, top_n + 10)
            channel_ids.update(ids)
        except HttpError as e:
            if e.resp.status in (403, 429):
                raise HTTPException(429, "Quota da YouTube API excedida. Tente novamente amanhã.")
            raise HTTPException(500, f"Erro na busca por nicho: {e}")

    # Busca por canal similar (2 unidades: 1 para resolve + 1 para search)
    if seed_channel and seed_channel.strip():
        try:
            seed_item = _resolve_channel_by_handle(service, seed_channel.strip())
            if seed_item:
                # Remove o próprio canal dos resultados
                channel_ids.discard(seed_item["id"])
                # Busca canais no mesmo nicho usando o título do canal semente
                seed_title = seed_item["snippet"].get("title", "")
                query = f"{seed_title} {nicho}".strip() if nicho.strip() else seed_title
                if query:
                    ids = _search_channels(service, query, idioma, top_n + 10)
                    channel_ids.update(ids)
                    channel_ids.discard(seed_item["id"])
        except HttpError as e:
            if e.resp.status in (403, 429):
                raise HTTPException(429, "Quota da YouTube API excedida. Tente novamente amanhã.")
            raise HTTPException(500, f"Erro na busca por canal similar: {e}")

    if not channel_ids:
        return []

    # Busca stats de todos de uma vez (1 unidade)
    try:
        items = _get_channels_stats(service, list(channel_ids))
    except HttpError as e:
        if e.resp.status in (403, 429):
            raise HTTPException(429, "Quota da YouTube API excedida. Tente novamente amanhã.")
        raise HTTPException(500, f"Erro ao buscar estatísticas dos canais: {e}")

    candidatos = [c for item in items if (c := _build_candidato(item, filtros)) is not None]
    candidatos.sort(key=lambda c: c.score, reverse=True)
    return candidatos[:top_n]
