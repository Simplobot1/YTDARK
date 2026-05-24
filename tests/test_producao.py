from unittest.mock import MagicMock, patch

from app.models.canal import CanalConfig, ChannelDNA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_chat_response(content_text: str):
    """Build a fake OpenAI chat.completions response object."""
    msg = MagicMock()
    msg.content = content_text
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _fake_image_response(url: str):
    """Build a fake OpenAI images.generate response object."""
    datum = MagicMock()
    datum.url = url
    response = MagicMock()
    response.data = [datum]
    return response


def _make_dna() -> ChannelDNA:
    return ChannelDNA(
        estilo_visual="whiteboard",
        tom_voz="casual and educational",
        paleta_cores=["#FF6B35", "#FFFFFF", "#2C3E50"],
        intro_max_sec=30,
        hook_style="bold question or shocking stat",
        num_pontos=5,
        cta_style="subscribe + next video suggestion",
        thumbnail_formula="bold text left + visual right",
        thumbnail_fonte="Montserrat Bold",
        titulo_formula="[Number] Ways to [Benefit] (No [Common Excuse])",
        duracao_alvo_min=12,
    )


def _make_config(tipo_padrao: str = "whiteboard") -> CanalConfig:
    return CanalConfig(
        canal_id="mofmoney",
        youtube_handle="@mofmoney",
        idioma="en",
        nicho_keywords=["investing", "personal finance", "money", "stocks"],
        tipo_video_padrao=tipo_padrao,
    )


# ---------------------------------------------------------------------------
# gerar_roteiro
# ---------------------------------------------------------------------------


@patch("app.services.roteirista.OpenAI")
def test_gerar_roteiro_loads_whiteboard_template_and_calls_openai(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_chat_response(
        "[TÍTULO] 5 Ways to Build Wealth\n[HOOK]...\n[CTA] Subscribe."
    )
    mock_openai_cls.return_value = mock_client

    from app.services.roteirista import gerar_roteiro

    analise = {
        "tipo_video": "whiteboard",
        "tema_central": "Investing mistakes to avoid",
        "angulo_conteudo": "beginner-friendly with practical examples",
    }
    dna = _make_dna()
    config = _make_config()

    result = gerar_roteiro(analise, dna, config)

    assert "5 Ways to Build Wealth" in result
    mock_client.chat.completions.create.assert_called_once()

    # The call was made with gpt-4o and a prompt containing template substitutions
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-4o"
    assert kwargs["max_tokens"] == 3000

    prompt = kwargs["messages"][0]["content"]
    # Template placeholders were substituted
    assert "{tema_central}" not in prompt
    assert "{tom_voz}" not in prompt
    assert "Investing mistakes to avoid" in prompt
    assert "beginner-friendly with practical examples" in prompt
    assert "casual and educational" in prompt
    # nicho_keywords first 3 joined
    assert "investing personal finance money" in prompt
    # Whiteboard-specific structure marker
    assert "WHITEBOARD" in prompt


@patch("app.services.roteirista.OpenAI")
def test_gerar_roteiro_falls_back_to_tipo_padrao_when_tipo_video_missing(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_chat_response("roteiro")
    mock_openai_cls.return_value = mock_client

    from app.services.roteirista import gerar_roteiro, _load_prompt_template

    # analise has no 'tipo_video' key
    analise = {
        "tema_central": "Crypto basics",
        "angulo_conteudo": "very beginner friendly",
    }
    dna = _make_dna()
    config = _make_config(tipo_padrao="talking_head")

    result = gerar_roteiro(analise, dna, config)
    assert result == "roteiro"

    # The prompt must come from the talking_head template
    expected_template = _load_prompt_template("talking_head")
    _, kwargs = mock_client.chat.completions.create.call_args
    prompt = kwargs["messages"][0]["content"]

    # talking_head template uses "TALKING HEAD" wording, whiteboard uses "WHITEBOARD"
    assert "TALKING HEAD" in expected_template
    assert "TALKING HEAD" in prompt
    assert "WHITEBOARD" not in prompt


# ---------------------------------------------------------------------------
# gerar_thumbnail
# ---------------------------------------------------------------------------


@patch("app.services.thumbnail.httpx.Client")
@patch("app.services.thumbnail.OpenAI")
def test_gerar_thumbnail_calls_dalle3_and_downloads_image(mock_openai_cls, mock_httpx_cls, tmp_path, monkeypatch):
    # Redirect TEMP_DIR to a pytest tmp_path so we don't touch the real temp/ folder
    monkeypatch.setattr("app.services.thumbnail.TEMP_DIR", str(tmp_path))

    mock_client = MagicMock()
    mock_client.images.generate.return_value = _fake_image_response(
        "https://example.com/fake-image.png"
    )
    mock_openai_cls.return_value = mock_client

    # Mock httpx Client context manager to return fake image bytes
    fake_bytes = b"\xff\xd8\xff\xe0fakejpegbytes"
    mock_resp = MagicMock()
    mock_resp.content = fake_bytes

    mock_http = MagicMock()
    mock_http.get.return_value = mock_resp
    mock_httpx_cls.return_value.__enter__.return_value = mock_http

    from app.services.thumbnail import gerar_thumbnail

    dna = _make_dna()
    titulo = "5 Ways to Build Wealth"
    video_id = "vid123"

    dest = gerar_thumbnail(titulo, dna, video_id)

    # File should be saved at tmp_path/vid123_thumbnail.jpg
    expected_path = str(tmp_path / "vid123_thumbnail.jpg")
    assert dest == expected_path

    import os
    assert os.path.isfile(expected_path)
    with open(expected_path, "rb") as f:
        assert f.read() == fake_bytes

    # DALL-E 3 was called with the right params
    mock_client.images.generate.assert_called_once()
    _, kwargs = mock_client.images.generate.call_args
    assert kwargs["model"] == "dall-e-3"
    assert kwargs["size"] == "1792x1024"
    assert kwargs["quality"] == "standard"
    assert kwargs["n"] == 1

    # Prompt incorporates DNA fields and the video title
    prompt = kwargs["prompt"]
    assert titulo in prompt
    assert dna.thumbnail_formula in prompt
    assert dna.thumbnail_fonte in prompt
    # First two colors are present
    assert "#FF6B35" in prompt
    assert "#FFFFFF" in prompt
    # 16:9 marker
    assert "16:9" in prompt

    # Image was downloaded from the URL returned by DALL-E
    mock_http.get.assert_called_once_with("https://example.com/fake-image.png")
