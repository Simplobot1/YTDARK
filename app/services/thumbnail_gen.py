"""Geração de thumbnails via Together AI (FLUX) ou DALL-E 3."""

import os
import httpx
from app.config import get_settings


TEMP_DIR = "temp"


def construir_prompt_thumbnail(estrutura_thumb: str, titulo: str) -> str:
    """Constrói prompt de imagem baseado na análise da thumbnail do canal fonte."""
    estilo = (estrutura_thumb or "")[:200].strip() or "dramatic dark cinematic style"
    tema = (titulo or "")[:100].strip() or "mysterious story"
    return (
        f"YouTube thumbnail image. Style: {estilo}. "
        f"Theme: {tema}. "
        "Cinematic lighting, high contrast, dramatic mood. No text in image. 16:9 aspect ratio."
    )


def gerar_thumbnail(prompt: str, video_id: str, canal_id: str, provider: str = "together") -> str:
    """Gera thumbnail e salva em temp/{canal_id}/{video_id}/thumbnail.jpg.

    Args:
        prompt: Prompt já montado para o gerador.
        video_id: ID do vídeo.
        canal_id: ID do canal (define subpath).
        provider: "together" (FLUX) ou "dalle" (DALL-E 3).
    """
    out_dir = os.path.join(TEMP_DIR, canal_id, video_id)
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "thumbnail.jpg")

    if provider == "together":
        return _gerar_together(prompt, dest)
    elif provider == "dalle":
        return _gerar_dalle(prompt, dest)
    raise ValueError(f"provider desconhecido: {provider}")


def _gerar_together(prompt: str, dest: str) -> str:
    settings = get_settings()
    if not settings.together_ai_key:
        raise RuntimeError("together_ai_key não configurada")
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            "https://api.together.xyz/v1/images/generations",
            headers={"Authorization": f"Bearer {settings.together_ai_key}"},
            json={
                "model": "black-forest-labs/FLUX.1-schnell-Free",
                "prompt": prompt,
                "width": 1440,
                "height": 1440,
                "steps": 4,
                "n": 1,
                "guidance": 3.5,
                "output_format": "jpeg",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        img_url = data["data"][0]["url"]
        r = client.get(img_url)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
    return dest


def _gerar_dalle(prompt: str, dest: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=get_settings().openai_api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    with httpx.Client(timeout=60) as c:
        r = c.get(image_url)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
    return dest
