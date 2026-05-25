"""Analisa o vídeo fonte: padrão de títulos, estrutura de roteiro e estilo de thumbnail.

Usa GPT-4o com input multimodal (texto + imagem) para extrair os 3 padrões
que serão usados pelo roteirista e gerador de thumbnail.
"""

import json
import re
import httpx
from typing import Dict
from openai import OpenAI
from app.config import get_settings


def _thumb_url(video_id: str) -> str:
    """Retorna URL da melhor thumb disponível (maxres → hq fallback)."""
    primary = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    fallback = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    try:
        r = httpx.get(primary, timeout=5)
        if r.status_code == 200 and len(r.content) > 1000:
            return primary
    except Exception:
        pass
    return fallback


def _strip_markdown_fences(raw: str) -> str:
    """Remove cercas ```json / ``` que GPT às vezes envia."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def analisar_video(titulo: str, transcricao: str, video_id: str) -> Dict[str, str]:
    """Analisa um vídeo. Retorna dict com prompt_titulo, estrutura_video e estrutura_thumb."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    thumb_url = _thumb_url(video_id)

    # ─── 1. Análise de título + estrutura de roteiro (texto + thumb opcional) ──
    prompt_analise = f"""Analise este vídeo do YouTube e retorne um JSON com exatamente 2 campos.

Título do vídeo: {titulo}

Transcrição (primeiros 3000 chars):
{transcricao[:3000]}

Retorne APENAS este JSON (sem markdown, sem ```):
{{
  "prompt_titulo": "descreva o PADRÃO do título: estrutura, palavras-chave, emoção, fórmula replicável (use português)",
  "estrutura_video": "descreva em tópicos: hook (abertura), blocos principais, transições, CTA, ritmo narrativo (use português)"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_analise},
                    {"type": "image_url", "image_url": {"url": thumb_url, "detail": "low"}},
                ],
            }
        ],
        max_tokens=1000,
    )

    raw = _strip_markdown_fences(response.choices[0].message.content)
    try:
        resultado = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: resposta não veio em JSON — divide texto pela metade.
        meio = len(raw) // 2
        resultado = {
            "prompt_titulo": raw[:meio].strip()[:500] or "padrão narrativo dramático",
            "estrutura_video": raw[meio:].strip()[:800] or "introdução + blocos + conclusão provocativa",
        }

    # ─── 2. Análise dedicada da thumbnail (visual) ───────────────────────────
    resp_thumb = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analise esta thumbnail de YouTube. Descreva em 3-5 frases diretas: "
                            "cores dominantes, estilo de fonte (se houver texto), layout (posição do texto/rosto), "
                            "elementos visuais, emoção transmitida. Responda em português."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": thumb_url, "detail": "low"}},
                ],
            }
        ],
        max_tokens=300,
    )
    resultado["estrutura_thumb"] = resp_thumb.choices[0].message.content.strip()

    return {
        "prompt_titulo": resultado.get("prompt_titulo", ""),
        "estrutura_video": resultado.get("estrutura_video", ""),
        "estrutura_thumb": resultado.get("estrutura_thumb", ""),
    }
