from typing import List, Optional
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig
from app.config import get_settings
import re

def _parse_iso_duration_to_min(iso: str) -> float:
    h = int(re.search(r"(\d+)H", iso).group(1)) if "H" in iso else 0
    m = int(re.search(r"(\d+)M", iso).group(1)) if "M" in iso else 0
    s = int(re.search(r"(\d+)S", iso).group(1)) if "S" in iso else 0
    return h * 60 + m + s / 60

def _calc_video_score(views: int, likes: int, comments: int, duration_min: float,
                      canal_avg_views: float, keywords: List[str], titulo: str) -> float:
    views_ratio = min(views / max(canal_avg_views, 1), 3.0) / 3.0 * 40
    eng = (likes + comments) / max(views, 1) * 100
    engagement = min(eng / 10.0, 1.0) * 30
    titulo_lower = titulo.lower()
    keyword_hits = sum(1 for kw in keywords if kw.lower() in titulo_lower)
    keyword_fit = min(keyword_hits / max(len(keywords), 1), 1.0) * 20
    dna_fit = 10.0 if 8 <= duration_min <= 20 else 5.0
    return round(views_ratio + engagement + keyword_fit + dna_fit, 2)

def _resolve_channel_id(service, handle: str) -> Optional[str]:
    """Resolve @handle para channel_id do YouTube."""
    clean = handle.lstrip("@")
    try:
        resp = service.channels().list(part="id", forHandle=clean).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["id"]
    except Exception:
        pass
    # fallback: busca por username
    try:
        resp = service.channels().list(part="id", forUsername=clean).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["id"]
    except Exception:
        pass
    return None

def _get_channel_avg_views(service, channel_id: str) -> float:
    try:
        resp = service.channels().list(part="statistics", id=channel_id).execute()
        items = resp.get("items", [])
        if items:
            stats = items[0]["statistics"]
            total = int(stats.get("viewCount", 0))
            count = max(int(stats.get("videoCount", 1)), 1)
            return total / count
    except Exception:
        pass
    return 100_000.0

def _mine_from_channel(service, channel_id: str, source_label: str,
                       config: CanalConfig, since: str, avg_views: float) -> List[Video]:
    """Busca vídeos diretamente DO canal pelo channelId."""
    f = config.filtros_mineracao
    try:
        search_resp = service.search().list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="viewCount",
            publishedAfter=since,
            videoDuration="medium",
            maxResults=15,
        ).execute()
    except Exception:
        return []

    video_ids = [i["id"]["videoId"] for i in search_resp.get("items", [])]
    if not video_ids:
        return []

    try:
        vids_resp = service.videos().list(
            part="statistics,contentDetails,snippet",
            id=",".join(video_ids),
        ).execute()
    except Exception:
        return []

    results = []
    for v in vids_resp.get("items", []):
        stats = v["statistics"]
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        duration_min = _parse_iso_duration_to_min(v["contentDetails"]["duration"])

        if views < f.min_views:
            continue
        if not (f.duracao_min_min <= duration_min <= f.duracao_max_min):
            continue

        score = _calc_video_score(
            views, likes, comments, duration_min,
            avg_views, config.nicho_keywords,
            v["snippet"]["title"],
        )
        results.append(Video(
            video_id=v["id"],
            titulo=v["snippet"]["title"],
            canal_fonte=source_label,
            views=views,
            data_pub=v["snippet"]["publishedAt"][:10],
            duracao_min=round(duration_min, 1),
            tipo=config.tipo_video_padrao,
            score=score,
            status=VideoStatus.CANDIDATO,
        ))
    return results

def _mine_by_keywords(service, config: CanalConfig, since: str) -> List[Video]:
    """Fallback: busca por keywords do nicho quando não há canais fonte."""
    f = config.filtros_mineracao
    query = " ".join(config.nicho_keywords)
    if not query.strip():
        return []
    try:
        search_resp = service.search().list(
            part="snippet",
            q=query,
            type="video",
            order="viewCount",
            publishedAfter=since,
            videoDuration="medium",
            relevanceLanguage=config.idioma,
            maxResults=15,
        ).execute()
    except Exception:
        return []

    video_ids = [i["id"]["videoId"] for i in search_resp.get("items", [])]
    if not video_ids:
        return []

    try:
        vids_resp = service.videos().list(
            part="statistics,contentDetails,snippet",
            id=",".join(video_ids),
        ).execute()
    except Exception:
        return []

    results = []
    for v in vids_resp.get("items", []):
        stats = v["statistics"]
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        duration_min = _parse_iso_duration_to_min(v["contentDetails"]["duration"])

        if views < f.min_views:
            continue
        if not (f.duracao_min_min <= duration_min <= f.duracao_max_min):
            continue

        score = _calc_video_score(views, likes, comments, duration_min,
                                   100_000, config.nicho_keywords,
                                   v["snippet"]["title"])
        results.append(Video(
            video_id=v["id"],
            titulo=v["snippet"]["title"],
            canal_fonte="nicho:" + config.nicho_keywords[0] if config.nicho_keywords else "busca",
            views=views,
            data_pub=v["snippet"]["publishedAt"][:10],
            duracao_min=round(duration_min, 1),
            tipo=config.tipo_video_padrao,
            score=score,
            status=VideoStatus.CANDIDATO,
        ))
    return results

def minerar_canal(config: CanalConfig) -> List[Video]:
    service = build("youtube", "v3", developerKey=get_settings().youtube_api_key)
    f = config.filtros_mineracao
    since = (datetime.utcnow() - timedelta(days=f.max_dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    videos: List[Video] = []
    seen_ids: set = set()

    if config.canais_fonte:
        for handle in config.canais_fonte:
            try:
                channel_id = _resolve_channel_id(service, handle)
                if not channel_id:
                    continue
                avg_views = _get_channel_avg_views(service, channel_id)
                for v in _mine_from_channel(service, channel_id, handle, config, since, avg_views):
                    if v.video_id not in seen_ids:
                        seen_ids.add(v.video_id)
                        videos.append(v)
            except Exception:
                continue
    else:
        for v in _mine_by_keywords(service, config, since):
            if v.video_id not in seen_ids:
                seen_ids.add(v.video_id)
                videos.append(v)

    videos.sort(key=lambda v: v.score, reverse=True)
    return videos
