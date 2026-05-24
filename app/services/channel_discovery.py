from typing import List, Optional
from googleapiclient.discovery import build
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings
from datetime import datetime, timedelta
import yt_dlp
import statistics
import re

def _get_yt_service():
    return build("youtube", "v3", developerKey=get_settings().youtube_api_key)

def _parse_duration_to_min(iso_duration: str) -> float:
    h = int(re.search(r"(\d+)H", iso_duration).group(1)) if "H" in iso_duration else 0
    m = int(re.search(r"(\d+)M", iso_duration).group(1)) if "M" in iso_duration else 0
    s = int(re.search(r"(\d+)S", iso_duration).group(1)) if "S" in iso_duration else 0
    return h * 60 + m + s / 60

def _calc_score(m: MetricasCanal) -> float:
    norm_views = min(m.avg_views / 500000, 1.0) * 40
    norm_eng = min(m.engagement_rate / 10.0, 1.0) * 30
    norm_freq = min(m.upload_freq_mensal / 12.0, 1.0) * 20
    norm_momentum = {"crescendo": 10, "estavel": 5, "declinando": 0}.get(m.momentum, 5)
    return round(norm_views + norm_eng + norm_freq + norm_momentum, 2)

def _get_channel_metrics(service, channel_id: str) -> Optional[MetricasCanal]:
    try:
        resp = service.channels().list(part="statistics,snippet", id=channel_id).execute()
        items = resp.get("items", [])
        if not items:
            return None
        stats = items[0]["statistics"]
        subscribers = int(stats.get("subscriberCount", 0))

        videos_resp = service.search().list(
            part="id", channelId=channel_id, type="video",
            order="date", maxResults=20
        ).execute()
        video_ids = [i["id"]["videoId"] for i in videos_resp.get("items", [])]
        if not video_ids:
            return None

        vids_resp = service.videos().list(
            part="statistics,contentDetails", id=",".join(video_ids)
        ).execute()

        views_list, eng_list, durations = [], [], []
        for v in vids_resp.get("items", []):
            s = v["statistics"]
            views = int(s.get("viewCount", 0))
            likes = int(s.get("likeCount", 0))
            comments = int(s.get("commentCount", 0))
            views_list.append(views)
            eng_list.append((likes + comments) / max(views, 1) * 100)
            durations.append(_parse_duration_to_min(v["contentDetails"]["duration"]))

        search_30d = service.search().list(
            part="snippet", channelId=channel_id, type="video", order="date", maxResults=4,
            publishedAfter=(datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ).execute()
        upload_freq = len(search_30d.get("items", []))

        avg_views_recent = statistics.mean(views_list[:5]) if len(views_list) >= 5 else statistics.mean(views_list) if views_list else 0
        avg_views_all = statistics.mean(views_list) if views_list else 0
        momentum = "crescendo" if avg_views_recent > avg_views_all * 1.1 else (
            "declinando" if avg_views_recent < avg_views_all * 0.9 else "estavel"
        )

        return MetricasCanal(
            subscribers=subscribers,
            avg_views=round(statistics.mean(views_list), 0) if views_list else 0,
            engagement_rate=round(statistics.mean(eng_list), 2) if eng_list else 0,
            upload_freq_mensal=upload_freq,
            avg_duration_min=round(statistics.mean(durations), 1) if durations else 0,
            momentum=momentum,
        )
    except Exception:
        return None

def _get_related_channels_ytdlp(seed_handle: str) -> List[str]:
    url = f"https://www.youtube.com/{seed_handle}/channels"
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", []) if info else []
            return [e.get("url", "") for e in entries if e.get("url")][:20]
    except Exception:
        return []

def discover_channels(
    estrategia: str,
    nicho: str,
    idioma: str,
    filtros: dict,
    top_n: int = 20,
    seed_channel: Optional[str] = None,
) -> List[CanalCandidato]:
    service = _get_yt_service()
    channel_ids = []

    if estrategia == "seed" and seed_channel:
        related_urls = _get_related_channels_ytdlp(seed_channel)
        for url in related_urls:
            if "channel/" in url:
                channel_ids.append(url.split("channel/")[-1])
            elif "@" in url or "/c/" in url:
                try:
                    r = service.search().list(part="snippet", q=url, type="channel", maxResults=1).execute()
                    for item in r.get("items", []):
                        channel_ids.append(item["snippet"]["channelId"])
                except Exception:
                    continue
    else:
        resp = service.search().list(
            part="snippet", q=nicho, type="channel",
            relevanceLanguage=idioma, maxResults=30
        ).execute()
        channel_ids = [i["snippet"]["channelId"] for i in resp.get("items", [])]

    candidatos = []
    for cid in set(channel_ids):
        metricas = _get_channel_metrics(service, cid)
        if not metricas:
            continue
        f = filtros
        if metricas.subscribers < f.get("subscribers_min", 0): continue
        if metricas.subscribers > f.get("subscribers_max", 999999999): continue
        if metricas.avg_views < f.get("avg_views_min", 0): continue
        if metricas.upload_freq_mensal < f.get("upload_freq_min", 0): continue
        if metricas.avg_duration_min < f.get("avg_duration_min_min", 0): continue
        if metricas.avg_duration_min > f.get("avg_duration_max_min", 999): continue

        try:
            resp = service.channels().list(part="snippet", id=cid).execute()
            snippet = resp["items"][0]["snippet"]
            handle = snippet.get("customUrl", f"@{snippet['title'].replace(' ','')}")
            if not handle.startswith("@"):
                handle = f"@{handle}"
        except Exception:
            handle = f"@{cid[:10]}"
            snippet = {"title": cid}

        candidatos.append(CanalCandidato(
            handle=handle,
            nome=snippet.get("title", cid),
            channel_id=cid,
            metricas=metricas,
            score=_calc_score(metricas)
        ))

    candidatos.sort(key=lambda c: c.score, reverse=True)
    return candidatos[:top_n]
