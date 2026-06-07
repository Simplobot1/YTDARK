import subprocess
import json
import os


def download_video(url: str, output_dir: str = "/tmp/ytdark") -> dict:
    """Baixa vídeo e retorna metadados + caminho local."""
    os.makedirs(output_dir, exist_ok=True)

    meta_result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True, text=True, timeout=60,
    )
    if meta_result.returncode != 0:
        raise RuntimeError(f"yt-dlp metadata falhou: {meta_result.stderr}")

    meta = json.loads(meta_result.stdout)
    video_id = meta["id"]
    ext = meta.get("ext", "mp4")
    output_path = os.path.join(output_dir, f"{video_id}.{ext}")

    dl_result = subprocess.run(
        ["yt-dlp", "--no-playlist", "-o", output_path, url],
        capture_output=True, text=True, timeout=600,
    )
    if dl_result.returncode != 0:
        raise RuntimeError(f"yt-dlp download falhou: {dl_result.stderr}")

    return {
        "video_id": video_id,
        "title": meta.get("title", ""),
        "duration": meta.get("duration", 0),
        "channel": meta.get("channel", ""),
        "view_count": meta.get("view_count", 0),
        "path": output_path,
    }


def get_channel_related(handle: str) -> list[dict]:
    """Busca canais relacionados/featured de um canal via yt-dlp."""
    url = f"https://www.youtube.com/{handle}"
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--flat-playlist", "--no-warnings", url],
        capture_output=True, text=True, timeout=60,
    )
    channels = []
    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
            if data.get("_type") == "url" and "channel" in data.get("url", ""):
                channels.append({
                    "url": data["url"],
                    "title": data.get("title", ""),
                })
        except json.JSONDecodeError:
            continue
    return channels
