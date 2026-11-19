"""Testes do cálculo de estimativa de espera."""

from app.services.guidance_engine import compute_wait_estimate


def test_insufficient_data_is_not_invented():
    result = compute_wait_estimate([20, 30], waiting_count=5, professionals_available=3)
    assert result["is_reliable"] is False
    assert result["low_minutes"] is None
    assert "dados suficientes" in result["message"].lower()


def test_zero_professionals_is_unreliable():
    result = compute_wait_estimate([20, 25, 30, 35, 40], waiting_count=5, professionals_available=0)
    assert result["is_reliable"] is False


def test_estimate_range_and_median():
    durations = [20, 25, 30, 35, 40]
    result = compute_wait_estimate(durations, waiting_count=4, professionals_available=2)
    assert result["is_reliable"] is True
    assert result["sample_size"] == 5
    assert result["p50_minutes"] == 30
    assert result["low_minutes"] >= 0
    assert result["high_minutes"] > result["low_minutes"]
    # throughput = 2 * (60/30) = 4 pacientes/h -> 4 aguardando = 60 min
    assert result["high_minutes"] >= 60


def test_no_waiting_shows_zero_without_precision():
    result = compute_wait_estimate([20, 25, 30, 35, 40], waiting_count=0, professionals_available=2)
    assert result["is_reliable"] is True
    assert result["low_minutes"] == 0
    assert "aguardando" in result["message"].lower()


def test_capacity_change_changes_estimate():
    base = compute_wait_estimate([20, 25, 30, 35, 40], waiting_count=4, professionals_available=2)
    reduced = compute_wait_estimate([20, 25, 30, 35, 40], waiting_count=4, professionals_available=1)
    assert reduced["high_minutes"] > base["high_minutes"]


def test_rounding_to_five_minutes():
    result = compute_wait_estimate([17, 19, 23, 29, 31], waiting_count=3, professionals_available=2)
    for key in ("low_minutes", "p50_minutes", "high_minutes"):
        assert result[key] % 5 == 0
