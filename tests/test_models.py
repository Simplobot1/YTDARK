from app.models.video import Video, VideoStatus
from app.models.canal import CanalConfig, ChannelDNA
from app.models.canal_candidato import CanalCandidato, MetricasCanal

def test_video_default_status():
    v = Video(video_id="abc123", titulo="Test", canal_fonte="@test",
              views=100000, data_pub="2026-05-01", duracao_min=12.5)
    assert v.status == VideoStatus.CANDIDATO
    assert v.score == 0.0

def test_video_status_enum_values():
    assert VideoStatus.CANDIDATO == "candidato"
    assert VideoStatus.PUBLICADO == "publicado"

def test_canal_config_defaults():
    c = CanalConfig(canal_id="test", youtube_handle="@test")
    assert c.idioma == "en"
    assert c.tipo_video_padrao == "whiteboard"
    assert c.filtros_mineracao.min_views == 50000

def test_channel_dna_defaults():
    dna = ChannelDNA()
    assert dna.num_pontos == 5
    assert len(dna.paleta_cores) == 3

def test_canal_candidato_score():
    m = MetricasCanal(subscribers=500000, avg_views=120000,
                      engagement_rate=4.5, upload_freq_mensal=8,
                      avg_duration_min=14, momentum="crescendo")
    c = CanalCandidato(handle="@test", nome="Test Channel",
                       channel_id="UC123", metricas=m, score=87.5)
    assert c.score == 87.5
    assert not c.adicionado
