"""Tests for the production/publication pipeline: narrador, editor, producao, publicacao."""
import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth import verify_token
from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig, ChannelDNA


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def _override_auth():
    return "test@user.com"


app.dependency_overrides[verify_token] = _override_auth
client = TestClient(app)


def _make_video(status: VideoStatus = VideoStatus.ANALISADO, **extra) -> Video:
    v = Video(
        video_id="vid123",
        titulo="How to Invest",
        canal_fonte="@nickinvestsUS",
        views=120000,
        data_pub="2026-05-10",
        duracao_min=12.0,
        score=82.0,
        status=status,
        analise={
            "tipo_video": "whiteboard",
            "tema_central": "Investing mistakes to avoid",
            "angulo_conteudo": "beginner-friendly with practical examples",
        },
    )
    for k, val in extra.items():
        setattr(v, k, val)
    return v


def _make_config(drive_folder: str = "") -> CanalConfig:
    return CanalConfig(
        canal_id="mofmoney",
        youtube_handle="@mofmoney",
        idioma="en",
        nicho_keywords=["personal finance", "investing", "passive income"],
        google_sheets_id="fake_sheets_id",
        google_drive_folder_id=drive_folder,
    )


def _make_dna() -> ChannelDNA:
    return ChannelDNA()


# ---------------------------------------------------------------------------
# narrador._extract_narration
# ---------------------------------------------------------------------------


def test_extract_narration_strips_bracket_tag_lines():
    from app.services.narrador import _extract_narration

    roteiro = (
        "[TITULO]\n"
        "5 Ways to Build Wealth\n"
        "[HOOK]\n"
        "Did you know most people never invest a single dollar?\n"
        "[PONTO 1]\n"
        "Start by saving 10% of every paycheck.\n"
        "[CTA]\n"
        "Subscribe for more tips."
    )
    result = _extract_narration(roteiro)

    # Bracket-only lines must be stripped
    assert "[TITULO]" not in result
    assert "[HOOK]" not in result
    assert "[PONTO 1]" not in result
    assert "[CTA]" not in result

    # Narration lines must remain, joined by single spaces
    assert "5 Ways to Build Wealth" in result
    assert "Did you know most people never invest a single dollar?" in result
    assert "Start by saving 10% of every paycheck." in result
    assert "Subscribe for more tips." in result


def test_extract_narration_keeps_blank_lines_out():
    from app.services.narrador import _extract_narration

    roteiro = "[INTRO]\n\nHello there.\n\n[OUTRO]\n\nGoodbye."
    result = _extract_narration(roteiro)
    assert result == "Hello there. Goodbye."


# ---------------------------------------------------------------------------
# narrador.gerar_narracao
# ---------------------------------------------------------------------------


@patch("app.services.narrador.ElevenLabs")
def test_gerar_narracao_calls_elevenlabs_and_saves_mp3(mock_eleven_cls, tmp_path, monkeypatch):
    # Redirect TEMP_DIR so we don't pollute the real temp folder
    monkeypatch.setattr("app.services.narrador.TEMP_DIR", str(tmp_path))

    mock_client = MagicMock()
    # generate() returns an iterable of audio byte chunks
    mock_client.generate.return_value = iter([b"\xff\xfb\x90", b"audio", b"chunks"])
    mock_eleven_cls.return_value = mock_client

    from app.services.narrador import gerar_narracao

    roteiro = "[TITULO]\nTest Video\nHello world.\n[CTA]"
    dest = gerar_narracao(roteiro, "vid123")

    expected_path = str(tmp_path / "vid123.mp3")
    assert dest == expected_path
    assert os.path.isfile(expected_path)
    with open(expected_path, "rb") as f:
        assert f.read() == b"\xff\xfb\x90audiochunks"

    # ElevenLabs was called with the narration-only text (no bracket-tag lines)
    mock_client.generate.assert_called_once()
    _, kwargs = mock_client.generate.call_args
    assert kwargs["model"] == "eleven_multilingual_v2"
    assert "Hello world." in kwargs["text"]
    assert "Test Video" in kwargs["text"]
    assert "[TITULO]" not in kwargs["text"]
    assert "[CTA]" not in kwargs["text"]


# ---------------------------------------------------------------------------
# editor.montar_video
# ---------------------------------------------------------------------------


@patch("app.services.editor.time.sleep", return_value=None)
@patch("app.services.editor.httpx.Client")
def test_montar_video_renders_with_shotstack_and_polls(mock_httpx_cls, _mock_sleep):
    # Two distinct contexts:
    #  - POST /render returns the render id
    #  - GET /render/{id} polls until "done"
    post_resp = MagicMock()
    post_resp.json.return_value = {"response": {"id": "render_abc"}}
    post_resp.raise_for_status.return_value = None

    poll_resp_done = MagicMock()
    poll_resp_done.json.return_value = {
        "response": {"status": "done", "url": "https://shotstack.io/out/render_abc.mp4"}
    }

    mock_http = MagicMock()
    mock_http.post.return_value = post_resp
    mock_http.get.return_value = poll_resp_done
    mock_httpx_cls.return_value.__enter__.return_value = mock_http

    from app.services.editor import montar_video

    url = montar_video(
        tipo_template="whiteboard",
        audio_url="https://drive.example/audio.mp3",
        thumbnail_url="https://drive.example/thumb.jpg",
        titulo="5 Ways to Build Wealth",
        duracao_sec=180.5,
        video_id="vid123",
    )

    assert url == "https://shotstack.io/out/render_abc.mp4"

    # POST payload must have placeholders replaced
    mock_http.post.assert_called_once()
    _, post_kwargs = mock_http.post.call_args
    payload = post_kwargs["json"]
    payload_str = str(payload)
    assert "{{AUDIO_URL}}" not in payload_str
    assert "{{THUMBNAIL_URL}}" not in payload_str
    assert "{{TITULO}}" not in payload_str
    assert "{{DURACAO}}" not in payload_str
    assert "https://drive.example/audio.mp3" in payload_str
    assert "https://drive.example/thumb.jpg" in payload_str
    assert "5 Ways to Build Wealth" in payload_str

    # Duration was inserted as a number, not a string
    audio_clip = payload["timeline"]["tracks"][0]["clips"][0]
    assert audio_clip["length"] == 180.5

    # Polled at least once
    mock_http.get.assert_called()


@patch("app.services.editor.time.sleep", return_value=None)
@patch("app.services.editor.httpx.Client")
def test_montar_video_raises_when_shotstack_fails(mock_httpx_cls, _mock_sleep):
    post_resp = MagicMock()
    post_resp.json.return_value = {"response": {"id": "render_xyz"}}
    post_resp.raise_for_status.return_value = None

    failed_resp = MagicMock()
    failed_resp.json.return_value = {
        "response": {"status": "failed", "error": "asset unreachable"}
    }

    mock_http = MagicMock()
    mock_http.post.return_value = post_resp
    mock_http.get.return_value = failed_resp
    mock_httpx_cls.return_value.__enter__.return_value = mock_http

    from app.services.editor import montar_video
    import pytest

    with pytest.raises(RuntimeError, match="Shotstack render falhou"):
        montar_video(
            tipo_template="whiteboard",
            audio_url="a",
            thumbnail_url="t",
            titulo="x",
            duracao_sec=10.0,
            video_id="vid",
        )


# ---------------------------------------------------------------------------
# POST /canais/{canal_id}/produzir/{video_id}
# ---------------------------------------------------------------------------


@patch("app.routes.producao.montar_video")
@patch("app.routes.producao.gerar_narracao")
@patch("app.routes.producao.gerar_thumbnail")
@patch("app.routes.producao.gerar_roteiro")
@patch("app.routes.producao.upload_file")
@patch("app.routes.producao.SheetsDatabase")
@patch("app.routes.producao.get_dna")
@patch("app.routes.producao.get_config")
def test_produzir_video_runs_full_pipeline(
    mock_get_config,
    mock_get_dna,
    mock_db_cls,
    mock_upload,
    mock_roteiro,
    mock_thumbnail,
    mock_narracao,
    mock_montar,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)  # so temp/ writes happen inside tmp_path

    mock_get_config.return_value = _make_config(drive_folder="drive_xyz")
    mock_get_dna.return_value = _make_dna()
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = _make_video()
    mock_db_cls.return_value = mock_db

    mock_roteiro.return_value = "[TÍTULO] 5 Ways to Build Wealth\nHello.\n[CTA] Subscribe."
    mock_thumbnail.return_value = str(tmp_path / "vid123_thumb.jpg")
    # Create the thumbnail file so upload_file would find it
    (tmp_path / "vid123_thumb.jpg").write_bytes(b"img")
    mock_narracao.return_value = str(tmp_path / "vid123.mp3")
    (tmp_path / "vid123.mp3").write_bytes(b"audio")
    mock_montar.return_value = "https://shotstack.io/out/vid123.mp4"

    # upload_file returns a fake drive link for each call
    def _upload(path, folder, mime):
        return f"https://drive.example/{os.path.basename(path)}"
    mock_upload.side_effect = _upload

    resp = client.post("/canais/mofmoney/produzir/vid123")

    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["video_id"] == "vid123"
    assert body["status"] == "video_pronto"
    assert body["mp4_url"] == "https://shotstack.io/out/vid123.mp4"

    # All three services were called
    mock_roteiro.assert_called_once()
    mock_thumbnail.assert_called_once()
    mock_narracao.assert_called_once()
    mock_montar.assert_called_once()

    # Shotstack was called with the audio + thumbnail drive URLs
    _, montar_kwargs = mock_montar.call_args
    assert montar_kwargs["audio_url"].startswith("https://drive.example/")
    assert montar_kwargs["thumbnail_url"].startswith("https://drive.example/")
    assert montar_kwargs["tipo_template"] == "whiteboard"

    # DB updated with final status
    mock_db.atualizar_video.assert_called_once()
    updated = mock_db.atualizar_video.call_args[0][1]
    assert updated.status == VideoStatus.VIDEO_PRONTO
    assert updated.video_path == "https://shotstack.io/out/vid123.mp4"


@patch("app.routes.producao.SheetsDatabase")
@patch("app.routes.producao.get_dna")
@patch("app.routes.producao.get_config")
def test_produzir_video_400_when_not_analisado(mock_get_config, mock_get_dna, mock_db_cls):
    mock_get_config.return_value = _make_config()
    mock_get_dna.return_value = _make_dna()
    v = _make_video(status=VideoStatus.MINERADO)
    v.analise = None
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = v
    mock_db_cls.return_value = mock_db

    resp = client.post("/canais/mofmoney/produzir/vid123")
    assert resp.status_code == 400
    assert "analisado" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /canais/{canal_id}/publicar/{video_id}
# ---------------------------------------------------------------------------


@patch("app.routes.publicacao.publicar_video")
@patch("app.routes.publicacao.httpx.Client")
@patch("app.routes.publicacao.SheetsDatabase")
@patch("app.routes.publicacao.get_config")
def test_publicar_video_pronto_uploads_to_youtube(
    mock_get_config, mock_db_cls, mock_httpx_cls, mock_publicar, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    mock_get_config.return_value = _make_config()
    v = _make_video(status=VideoStatus.VIDEO_PRONTO)
    v.video_path = "https://shotstack.io/out/vid123.mp4"
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = v
    mock_db_cls.return_value = mock_db

    # httpx downloads the MP4
    mp4_resp = MagicMock()
    mp4_resp.content = b"\x00\x00\x00\x20ftypmp42fake-mp4"
    mock_http = MagicMock()
    mock_http.get.return_value = mp4_resp
    mock_httpx_cls.return_value.__enter__.return_value = mock_http

    mock_publicar.return_value = "https://www.youtube.com/watch?v=YT_ID"

    resp = client.post("/canais/mofmoney/publicar/vid123")

    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["yt_link"] == "https://www.youtube.com/watch?v=YT_ID"
    assert body["status"] == "publicado"

    # publicar_video was called with title, tags from nicho_keywords
    mock_publicar.assert_called_once()
    args, _ = mock_publicar.call_args
    titulo_arg, descricao_arg, tags_arg = args[1], args[2], args[3]
    assert titulo_arg == v.titulo
    assert "personal finance" in tags_arg
    assert "personal finance" in descricao_arg

    # Status was persisted
    updated = mock_db.atualizar_video.call_args[0][1]
    assert updated.status == VideoStatus.PUBLICADO
    assert updated.yt_link == "https://www.youtube.com/watch?v=YT_ID"


@patch("app.routes.publicacao.SheetsDatabase")
@patch("app.routes.publicacao.get_config")
def test_publicar_400_when_status_not_video_pronto(mock_get_config, mock_db_cls):
    mock_get_config.return_value = _make_config()
    v = _make_video(status=VideoStatus.AUDIO_GERADO)
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = v
    mock_db_cls.return_value = mock_db

    resp = client.post("/canais/mofmoney/publicar/vid123")
    assert resp.status_code == 400
    assert "video_pronto" in resp.json()["detail"]
