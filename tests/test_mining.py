import pytest
from app.services.minerador import _calc_video_score, _parse_iso_duration_to_min

def test_parse_duration_15min():
    assert _parse_iso_duration_to_min("PT15M") == 15.0

def test_parse_duration_1h10m30s():
    assert abs(_parse_iso_duration_to_min("PT1H10M30S") - 70.5) < 0.01

def test_score_viral_video():
    score = _calc_video_score(
        views=500000, likes=20000, comments=1000,
        duration_min=14.0, canal_avg_views=100000,
        keywords=["personal finance", "investing"],
        titulo="5 Investing Mistakes to Avoid in 2026"
    )
    assert score > 60

def test_score_bad_video():
    score = _calc_video_score(
        views=1000, likes=10, comments=2,
        duration_min=3.0, canal_avg_views=100000,
        keywords=["personal finance"],
        titulo="Random Video"
    )
    assert score < 20

def test_score_keyword_match_aumenta_score():
    score_match = _calc_video_score(500000, 15000, 800, 13.0, 100000,
                                    ["personal finance"], "Personal Finance Tips")
    score_no_match = _calc_video_score(500000, 15000, 800, 13.0, 100000,
                                       ["personal finance"], "Random Title")
    assert score_match > score_no_match
