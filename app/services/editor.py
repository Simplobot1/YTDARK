import json
import os
import time
import httpx
from app.config import get_settings

SHOTSTACK_BASE = "https://api.shotstack.io"


def _get_headers():
    settings = get_settings()
    env = settings.shotstack_env
    key = settings.shotstack_api_key
    return {
        "x-api-key": key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, env


def montar_video(tipo_template: str, audio_url: str, thumbnail_url: str,
                 titulo: str, duracao_sec: float, video_id: str) -> str:
    """Renderiza vídeo com Shotstack. Retorna URL do MP4 final."""
    template_path = os.path.join("templates", tipo_template, "shotstack.json")
    with open(template_path) as f:
        template = json.load(f)

    payload_str = json.dumps(template)
    payload_str = payload_str.replace("{{AUDIO_URL}}", audio_url)
    payload_str = payload_str.replace("{{THUMBNAIL_URL}}", thumbnail_url)
    payload_str = payload_str.replace("{{TITULO}}", titulo)
    payload_str = payload_str.replace('"{{DURACAO}}"', str(duracao_sec))
    payload = json.loads(payload_str)

    headers, env = _get_headers()
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{SHOTSTACK_BASE}/{env}/render", json=payload, headers=headers)
        resp.raise_for_status()
        render_id = resp.json()["response"]["id"]

    return _poll_render(render_id, headers, env)


def _poll_render(render_id: str, headers: dict, env: str) -> str:
    """Poll até render completar. Retorna URL do vídeo."""
    with httpx.Client(timeout=30) as client:
        for _ in range(60):
            time.sleep(10)
            resp = client.get(f"{SHOTSTACK_BASE}/{env}/render/{render_id}", headers=headers)
            data = resp.json()["response"]
            if data["status"] == "done":
                return data["url"]
            if data["status"] == "failed":
                raise RuntimeError(f"Shotstack render falhou: {data.get('error', 'unknown')}")
    raise TimeoutError("Shotstack render timeout após 10 minutos")
