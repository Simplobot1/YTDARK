import os
from app.config import get_settings
from app.models.canal import ChannelDNA, CanalConfig


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


def _load_prompt_template(tipo_video: str) -> str:
    path = os.path.join("templates", tipo_video, "prompt_roteiro.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()


def gerar_roteiro(analise: dict, dna: ChannelDNA, config: CanalConfig) -> str:
    """Gera roteiro original baseado na análise do vídeo e no DNA do canal."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    tipo = analise.get("tipo_video", config.tipo_video_padrao)
    prompt_template = _load_prompt_template(tipo)

    prompt = prompt_template.format(
        idioma=config.idioma,
        nicho=" ".join(config.nicho_keywords[:3]),
        tema_central=analise.get("tema_central", ""),
        angulo_conteudo=analise.get("angulo_conteudo", ""),
        tom_voz=dna.tom_voz,
        titulo_formula=dna.titulo_formula,
        num_pontos=dna.num_pontos,
        hook_style=dna.hook_style,
        cta_style=dna.cta_style,
        duracao_alvo_min=dna.duracao_alvo_min,
        intro_max_sec=dna.intro_max_sec,
        ponto="[PONTO]",
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
    )
    return response.choices[0].message.content.strip()
