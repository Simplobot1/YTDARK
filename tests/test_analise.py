from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.auth import verify_token
from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig


def _override_auth():
    return "test@user.com"


app.dependency_overrides[verify_token] = _override_auth
client = TestClient(app)


def _make_video():
    return Video(
        video_id="vid123",
        titulo="How to Invest",
        canal_fonte="@nickinvestsUS",
        views=120000,
        data_pub="2026-05-10",
        duracao_min=12.0,
        score=82.0,
        status=VideoStatus.MINERADO,
    )


def _make_config(drive_folder: str = "") -> CanalConfig:
    return CanalConfig(
        canal_id="mofmoney",
        youtube_handle="@mofmoney",
        idioma="en",
        google_sheets_id="fake_sheets_id",
        google_drive_folder_id=drive_folder,
    )


# ---------------------------------------------------------------------------
# Unit tests for analisar_frames
# ---------------------------------------------------------------------------


def _fake_openai_response(content_text: str):
    """Build a fake OpenAI chat.completions response object."""
    msg = MagicMock()
    msg.content = content_text
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("app.services.analisador._encode_image", return_value="ZmFrZQ==")
@patch("app.services.analisador.OpenAI")
def test_analisar_frames_retorna_dict(mock_openai_cls, _mock_encode):
    fake_analise = {
        "tipo_video": "whiteboard",
        "estrutura_roteiro": {"intro_segundos": 25, "num_pontos": 5, "tem_cta": True},
        "elementos_visuais": ["whiteboard", "marker"],
        "cores_dominantes": ["#FF6B35", "#FFFFFF"],
        "estilo_thumbnail": "bold left + visual right",
        "tema_central": "How to start investing",
        "angulo_conteudo": "beginner-friendly with practical examples",
    }
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_openai_response(
        _json.dumps(fake_analise)
    )
    mock_openai_cls.return_value = mock_client

    from app.services.analisador import analisar_frames
    result = analisar_frames(["frame1.jpg", "frame2.jpg"], "Hello investors...", "How to Invest")

    assert result == fake_analise
    mock_client.chat.completions.create.assert_called_once()


@patch("app.services.analisador._encode_image", return_value="ZmFrZQ==")
@patch("app.services.analisador.OpenAI")
def test_analisar_frames_handles_json_code_fences(mock_openai_cls, _mock_encode):
    fenced = """```json
{"tipo_video": "talking_head", "tema_central": "Crypto basics"}
```"""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_openai_response(fenced)
    mock_openai_cls.return_value = mock_client

    from app.services.analisador import analisar_frames
    result = analisar_frames(["frame1.jpg"], "Crypto intro", "Crypto Basics")

    assert result["tipo_video"] == "talking_head"
    assert result["tema_central"] == "Crypto basics"


@patch("app.services.analisador._encode_image", return_value="ZmFrZQ==")
@patch("app.services.analisador.OpenAI")
def test_analisar_frames_limits_to_6_frames(mock_openai_cls, _mock_encode):
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_openai_response(
        _json.dumps({"tipo_video": "whiteboard"})
    )
    mock_openai_cls.return_value = mock_client

    from app.services.analisador import analisar_frames
    analisar_frames([f"f{i}.jpg" for i in range(12)], "transcricao", "titulo")

    # The OpenAI call was made with 1 text block + at most 6 image blocks
    _, kwargs = mock_client.chat.completions.create.call_args
    content = kwargs["messages"][0]["content"]
    image_blocks = [c for c in content if c.get("type") == "image_url"]
    assert len(image_blocks) == 6


# ---------------------------------------------------------------------------
# Integration tests for the /analisar endpoint
# ---------------------------------------------------------------------------


@patch("app.routes.analise.cleanup_temp")
@patch("app.routes.analise.upload_file")
@patch("app.routes.analise.analisar_frames")
@patch("app.routes.analise.extract_frames")
@patch("app.routes.analise.transcrever")
@patch("app.routes.analise.download_audio")
@patch("app.routes.analise.SheetsDatabase")
@patch("app.routes.analise.get_config")
def test_analisar_video_sucesso(
    mock_get_config,
    mock_db_cls,
    mock_download_audio,
    mock_transcrever,
    mock_extract_frames,
    mock_analisar_frames,
    mock_upload_file,
    mock_cleanup,
):
    mock_get_config.return_value = _make_config(drive_folder="")
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = _make_video()
    mock_db_cls.return_value = mock_db

    mock_download_audio.return_value = "/tmp/vid123.mp3"
    mock_transcrever.return_value = "Hello investors, today we will talk about the top 5 investing mistakes you must avoid in 2026."
    mock_extract_frames.return_value = ["/tmp/vid123_frames/frame_001.jpg", "/tmp/vid123_frames/frame_002.jpg"]
    fake_analise = {
        "tipo_video": "whiteboard",
        "tema_central": "Investing mistakes to avoid",
    }
    mock_analisar_frames.return_value = fake_analise

    resp = client.post("/canais/mofmoney/analisar/vid123")

    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == "vid123"
    assert body["analise"] == fake_analise
    assert body["transcricao_preview"].startswith("Hello investors")
    assert len(body["transcricao_preview"]) <= 200

    # Side effects: video updated and temp cleaned
    mock_db.atualizar_video.assert_called_once()
    updated_video = mock_db.atualizar_video.call_args[0][1]
    assert updated_video.status == VideoStatus.ANALISADO
    assert updated_video.analise == fake_analise
    mock_cleanup.assert_called_once_with("vid123")
    # No drive folder configured → no uploads
    mock_upload_file.assert_not_called()


@patch("app.routes.analise.cleanup_temp")
@patch("app.routes.analise.upload_file")
@patch("app.routes.analise.analisar_frames")
@patch("app.routes.analise.extract_frames")
@patch("app.routes.analise.transcrever")
@patch("app.routes.analise.download_audio")
@patch("app.routes.analise.SheetsDatabase")
@patch("app.routes.analise.get_config")
def test_analisar_video_uploads_to_drive_when_folder_configured(
    mock_get_config,
    mock_db_cls,
    mock_download_audio,
    mock_transcrever,
    mock_extract_frames,
    mock_analisar_frames,
    mock_upload_file,
    mock_cleanup,
):
    mock_get_config.return_value = _make_config(drive_folder="drive_folder_xyz")
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = _make_video()
    mock_db_cls.return_value = mock_db

    mock_download_audio.return_value = "/tmp/vid123.mp3"
    mock_transcrever.return_value = "transcript"
    frames = ["/tmp/f1.jpg", "/tmp/f2.jpg", "/tmp/f3.jpg"]
    mock_extract_frames.return_value = frames
    mock_analisar_frames.return_value = {"tipo_video": "whiteboard"}

    resp = client.post("/canais/mofmoney/analisar/vid123")

    assert resp.status_code == 200
    assert mock_upload_file.call_count == len(frames)
    for call, frame in zip(mock_upload_file.call_args_list, frames):
        args, _ = call
        assert args[0] == frame
        assert args[1] == "drive_folder_xyz"


@patch("app.routes.analise.SheetsDatabase")
@patch("app.routes.analise.get_config")
def test_analisar_video_404_quando_nao_encontrado(mock_get_config, mock_db_cls):
    mock_get_config.return_value = _make_config()
    mock_db = MagicMock()
    mock_db.buscar_video.return_value = None
    mock_db_cls.return_value = mock_db

    resp = client.post("/canais/mofmoney/analisar/nonexistent")

    assert resp.status_code == 404
    assert "não encontrado" in resp.json()["detail"]


@patch("app.routes.analise.SheetsDatabase")
@patch("app.routes.analise.get_config")
def test_listar_analisados_filtra_por_status(mock_get_config, mock_db_cls):
    mock_get_config.return_value = _make_config()

    v_minerado = _make_video()
    v_analisado = _make_video()
    v_analisado.video_id = "vid999"
    v_analisado.status = VideoStatus.ANALISADO

    mock_db = MagicMock()
    mock_db.listar_candidatos.return_value = [v_minerado, v_analisado]
    mock_db_cls.return_value = mock_db

    resp = client.get("/canais/mofmoney/analisados")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["video_id"] == "vid999"
    assert body[0]["status"] == "analisado"
