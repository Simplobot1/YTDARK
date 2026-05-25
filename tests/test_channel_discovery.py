from app.services.channel_discovery import _calc_score


def test_calc_score_high_performer():
    # 1M subs + 500k avg_views -> ~100
    score = _calc_score(subs=1_000_000, avg_views=500_000)
    assert score > 70


def test_calc_score_low_performer():
    # 50k subs + 5k avg_views -> baixo
    score = _calc_score(subs=50_000, avg_views=5_000)
    assert score < 20


def test_calc_score_avg_views_dominates():
    a = _calc_score(subs=100_000, avg_views=500_000)
    b = _calc_score(subs=100_000, avg_views=50_000)
    assert a > b


def test_calc_score_subs_contributes():
    a = _calc_score(subs=1_000_000, avg_views=100_000)
    b = _calc_score(subs=50_000, avg_views=100_000)
    assert a > b
