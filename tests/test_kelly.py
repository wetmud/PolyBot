import pytest
from core.kelly import expected_value, kelly_fraction, fractional_kelly, position_size_usd


def test_expected_value_positive_edge():
    # p_hat=0.6, p=0.5 -> EV = 0.6 - 0.5 = 0.1
    assert abs(expected_value(0.6, 0.5) - 0.1) < 1e-12


def test_expected_value_no_edge():
    assert abs(expected_value(0.5, 0.5)) < 1e-12


def test_expected_value_negative_edge():
    assert expected_value(0.4, 0.5) < 0


def test_kelly_fraction_positive():
    # f* = (p_hat - p) / (1 - p)
    # p_hat=0.6, p=0.5 -> f* = 0.1 / 0.5 = 0.2
    result = kelly_fraction(0.6, 0.5)
    assert abs(result - 0.2) < 1e-12


def test_kelly_fraction_zero_ev():
    assert kelly_fraction(0.5, 0.5) == 0.0


def test_kelly_fraction_negative_ev():
    assert kelly_fraction(0.4, 0.5) == 0.0


def test_fractional_kelly_under_1hr():
    """< 1 hour -> 0.10x Kelly."""
    full_k = kelly_fraction(0.6, 0.5)  # 0.2
    frac = fractional_kelly(0.6, 0.5, market_duration_hours=0.5)
    assert abs(frac - full_k * 0.10) < 1e-12


def test_fractional_kelly_1_to_24hr():
    """1-24 hours -> 0.25x Kelly."""
    full_k = kelly_fraction(0.6, 0.5)
    frac = fractional_kelly(0.6, 0.5, market_duration_hours=12.0)
    assert abs(frac - full_k * 0.25) < 1e-12


def test_fractional_kelly_over_24hr():
    """> 24 hours -> 0.50x Kelly."""
    full_k = kelly_fraction(0.6, 0.5)
    frac = fractional_kelly(0.6, 0.5, market_duration_hours=48.0)
    assert abs(frac - full_k * 0.50) < 1e-12


def test_fractional_kelly_never_exceeds_half():
    """Even with huge edge, fractional Kelly <= 0.50 * full Kelly."""
    frac = fractional_kelly(0.99, 0.01, market_duration_hours=100.0)
    full_k = kelly_fraction(0.99, 0.01)
    assert frac <= full_k * 0.50 + 1e-12


def test_position_size_positive_ev():
    size = position_size_usd(bankroll=10_000, p_hat=0.6, p=0.5, market_duration_hours=12.0)
    assert size > 0


def test_position_size_zero_ev():
    size = position_size_usd(bankroll=10_000, p_hat=0.5, p=0.5, market_duration_hours=12.0)
    assert size == 0.0


def test_position_size_hard_cap():
    """Never risk more than max_position_pct of bankroll."""
    size = position_size_usd(
        bankroll=10_000, p_hat=0.99, p=0.01,
        market_duration_hours=100.0, max_position_pct=0.05
    )
    assert size <= 10_000 * 0.05 + 1e-6
