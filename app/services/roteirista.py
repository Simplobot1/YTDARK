"""Gera roteiro dark, título e SEO via GPT-4o."""

import json
import re
from typing import List
from app.config import get_settings


# Try to import OpenAI at module load. If the package is not installed
# (e.g. during unit tests), expose a placeholder so `patch("...OpenAI")`
# can still find and replace the attribute. The placeholder will raise
# if invoked unmocked.
try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    class OpenAI:  # type: ignore[no-redef]
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError(
                "openai package is not installed; install it to call the real API"
            )


DARK_SYSTEM_PROMPT = """You are a professional scriptwriter for YouTube dark/drama channels.

WRITING RULES:
- Length: 20,000-30,000 characters total
- Tone: mysterious, dramatic, conversational — like a great story being told
- Hook: start with a strong statement or question that grabs attention immediately
- Structure: Introduction + 6-8 informational blocks + Provocative conclusion
- Each block: starts with an impactful hook, ends with anticipation transition
- Transitions: "But that was just the beginning..." / "What happened next shocked everyone..."
- Language: short, strong, easy-to-understand sentences
- Style: dramatic but NOT sensationalist-sounding — natural, human
- NO: technical script language ("cut to...", "camera pans...", stage directions)
- NO: repetitive phrases — vary vocabulary constantly

CREATIVE CENSORSHIP (mandatory):
- "suicide" -> "off'd himself", "took his own life", "ended it all"
- "overdose" -> "OD'd", "went too far that night"
- "murder/killed" -> "ended", "took out"
- "accused of crime" -> "allegations surfaced", "accusations came to light"

DARK CONTENT RULES:
- Include: controversies, mysteries, unknown backstories, plot twists
- Focus on: rarely discussed aspects, recent controversies, rumors
- Use words: "revealed", "exposed", "jaw-dropping", "shocking" — but NOT forced
- Avoid: "the shocking truth" (overused) — vary phrasing

FORMAT: Write in continuous paragraphs like a great story. No bullet points. No headers."""


def _strip_markdown_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def gerar_roteiro(
    titulo: str,
    idioma: str,
    transcricao_ref: str = "",
    estrutura_ref: str = "",
) -> str:
    """Gera roteiro dark em 2 partes para produzir 20k-30k chars consistentes.

    Args:
        titulo: Título do novo vídeo.
        idioma: Código do idioma (ex: "en", "pt").
        transcricao_ref: Transcrição do vídeo fonte (inspiração estrutural — não copiar).
        estrutura_ref: Padrão de estrutura extraído do canal fonte.
    """
    client = OpenAI(api_key=get_settings().openai_api_key)

    contexto = ""
    if transcricao_ref:
        contexto += f"\n\nReference transcript (DO NOT copy, use as structural inspiration):\n{transcricao_ref[:2000]}"
    if estrutura_ref:
        contexto += f"\n\nChannel's video structure pattern:\n{estrutura_ref[:500]}"

    # ─── Parte 1 — abertura + meio, terminando em tensão ─────────────────────
    prompt_p1 = f"""Write PART 1 of a YouTube dark channel script.

Title: {titulo}
Language: {idioma}
{contexto}

Write approximately 12,000 characters. End at a moment of tension — do NOT resolve it.
Leave the audience wanting more. Return ONLY the script text, no labels."""

    resp1 = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": DARK_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_p1},
        ],
        max_tokens=4000,
    )
    parte1 = resp1.choices[0].message.content.strip()

    # ─── Parte 2 — continuação + conclusão ───────────────────────────────────
    ultimo_trecho = parte1[-500:] if len(parte1) > 500 else parte1

    prompt_p2 = f"""Continue this script EXACTLY from where it left off.

Story title: {titulo}
Language: {idioma}

Last part written:
{ultimo_trecho}

Continue naturally — DO NOT repeat anything above. Write the continuation and conclusion.
Target: 12,000-15,000 characters. End with a provocative, thought-provoking conclusion.
Return ONLY the continuation text, no labels."""

    resp2 = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": DARK_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_p2},
        ],
        max_tokens=4000,
    )
    parte2 = resp2.choices[0].message.content.strip()

    return parte1 + "\n\n" + parte2


def gerar_titulo(prompt_titulo_padrao: str, idioma: str) -> str:
    """Gera novo título seguindo o padrão extraído do canal fonte."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Generate a YouTube video title following this pattern:

{prompt_titulo_padrao}

Language: {idioma}
Rules: max 60 chars, no () or [], unique combination, never repeat previous titles, compelling.
Return ONLY the title.""",
            }
        ],
        max_tokens=100,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


def gerar_seo(titulo: str, roteiro: str, idioma: str, nicho_keywords: List[str]) -> dict:
    """Gera descrição SEO + tags otimizadas para o YouTube."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    keywords = ", ".join((nicho_keywords or [])[:5])
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Create YouTube SEO description and tags for:
Title: {titulo}
Language: {idioma}
Keywords: {keywords}
Script excerpt: {roteiro[:500]}

Return JSON only:
{{"descricao": "...(with hashtags, CTA, keywords, 300-500 chars)...", "tags": ["tag1","tag2", ...up to 15]}}
No markdown, no backticks.""",
            }
        ],
        max_tokens=600,
    )
    raw = _strip_markdown_fences(resp.choices[0].message.content)
    try:
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("not a dict")
        return {
            "descricao": str(result.get("descricao", titulo)),
            "tags": [str(t) for t in (result.get("tags") or (nicho_keywords or [])[:5])][:15],
        }
    except Exception:
        return {"descricao": titulo, "tags": (nicho_keywords or [])[:5]}
