from app.services.channel_discovery import _calc_score, _parse_duration_to_min
from app.models.canal_candidato import MetricasCanal

def test_parse_duration_12m30s():
    assert _parse_duration_to_min("PT12M30S") == 12.5

def test_parse_duration_1h5m():
    assert _parse_duration_to_min("PT1H5M") == 65.0

def test_parse_duration_only_minutes():
    assert _parse_duration_to_min("PT8M") == 8.0

def test_calc_score_high_performer():
    m = MetricasCanal(subscribers=1000000, avg_views=400000,
                      engagement_rate=5.0, upload_freq_mensal=10,
                      avg_duration_min=14, momentum="crescendo")
    assert _calc_score(m) > 70

def test_calc_score_low_performer():
    m = MetricasCanal(subscribers=50000, avg_views=5000,
                      engagement_rate=0.5, upload_freq_mensal=1,
                      avg_duration_min=5, momentum="declinando")
    assert _calc_score(m) < 20

def test_calc_score_momentum_crescendo_maior():
    base = dict(subscribers=500000, avg_views=100000, engagement_rate=3.0,
                upload_freq_mensal=6, avg_duration_min=12)
    assert _calc_score(MetricasCanal(**base, momentum="crescendo")) > _calc_score(MetricasCanal(**base, momentum="declinando"))
