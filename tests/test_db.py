from unittest.mock import MagicMock, patch
import gspread
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal

def _make_video():
    return Video(video_id="v001", titulo="Test Video", canal_fonte="@test",
                 views=100000, data_pub="2026-05-01", duracao_min=12.0,
                 score=85.0, status=VideoStatus.CANDIDATO)

@patch("app.services.sheets_impl.Credentials")
@patch("app.services.sheets_impl.gspread.authorize")
def test_salvar_video(mock_auth, mock_creds):
    mock_ws = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.worksheet.side_effect = gspread.WorksheetNotFound
    mock_sheet.add_worksheet.return_value = mock_ws
    mock_auth.return_value.open_by_key.return_value = mock_sheet
    mock_creds.from_service_account_file.return_value = MagicMock()

    from app.services.sheets_impl import SheetsDatabase
    db = SheetsDatabase("fake_id")
    db.salvar_video("mofmoney", _make_video())
    # add_worksheet append_row called once for headers, mock_ws append_row called once for video row
    assert mock_ws.append_row.call_count >= 1

@patch("app.services.sheets_impl.Credentials")
@patch("app.services.sheets_impl.gspread.authorize")
def test_listar_candidatos_vazio(mock_auth, mock_creds):
    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = []
    mock_sheet = MagicMock()
    mock_sheet.worksheet.return_value = mock_ws
    mock_auth.return_value.open_by_key.return_value = mock_sheet
    mock_creds.from_service_account_file.return_value = MagicMock()

    from app.services.sheets_impl import SheetsDatabase
    db = SheetsDatabase("fake_id")
    result = db.listar_candidatos("mofmoney")
    assert result == []
