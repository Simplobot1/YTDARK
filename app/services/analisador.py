import base64
import json
from typing import List
from app.config import get_settings


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# Try to import OpenAI at module load. If the package is not installed
# (e.g. during unit tests), expose a placeholder so `patch("...OpenAI")`
# can still find and replace the attribute. The placeholder will raise
# if invoked unmocked.
try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - exercised only in environments without openai
    class OpenAI:  # type: ignore[no-redef]
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError(
                "openai package is not installed; install it to call the real API"
            )


def analisar_frames(frames: List[str], transcricao: str, titulo: str) -> dict:
    """Analisa frames de um vídeo com GPT-4o Vision. Retorna estrutura de análise."""
    client = OpenAI(api_key=get_settings().openai_api_key)

    content = [
        {"type": "text", "text": (
            f"Você é um especialista em análise de conteúdo para YouTube.\n"
            f"Analise os frames deste vídeo intitulado '{titulo}'.\n"
            f"Transcrição parcial: {transcricao[:1000]}...\n\n"
            f"Retorne um JSON com:\n"
            f"- tipo_video: 'whiteboard' | 'talking_head' | 'slides'\n"
            f"- estrutura_roteiro: {{intro_segundos, num_pontos, tem_cta}}\n"
            f"- elementos_visuais: [lista de elementos observados]\n"
            f"- cores_dominantes: [lista de cores em hex]\n"
            f"- estilo_thumbnail: descrição do estilo visual\n"
            f"- tema_central: o tema principal do vídeo em 1 frase\n"
            f"- angulo_conteudo: qual o ângulo/perspectiva única deste vídeo\n"
            f"Responda APENAS com o JSON, sem texto extra."
        )}
    ]

    for frame_path in frames[:6]:
        img_b64 = _encode_image(frame_path)
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{img_b64}", "detail": "low"
        }})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
