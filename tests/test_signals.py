import numpy as np
import pytest
from core.signals import SignalDetector, Signal


def test_no_signal_when_prices_match():
    detector = SignalDetector(b=100_000, ev_threshold=0.02)
    q = np.array([0.0, 0.0])
    signal = detector.evaluate(
        q=q, market_price=0.50, bayesian_probability=0.50, duration_hours=24.0
    )
    assert signal is None


def test_buy_signal_when_market_underpriced():
    """Market price 0.40, Bayesian says 0.55 -> buy signal."""
    detector = SignalDetector(b=100_000, ev_threshold=0.02)
    q = np.array([0.0, 0.0])
    signal = detector.evaluate(
        q=q, market_price=0.40, bayesian_probability=0.55, duration_hours=24.0
    )
    assert signal is not None
    assert signal.side == "BUY"
    assert signal.ev > 0


def test_sell_signal_when_market_overpriced():
    """Market price 0.70, Bayesian says 0.50 -> sell/fade signal."""
    detector = SignalDetector(b=100_000, ev_threshold=0.02)
    q = np.array([0.0, 0.0])
    signal = detector.evaluate(
        q=q, market_price=0.70, bayesian_probability=0.50, duration_hours=24.0
    )
    assert signal is not None
    assert signal.side == "SELL"
    assert signal.ev > 0


def test_signal_contains_position_size():
    detector = SignalDetector(b=100_000, ev_threshold=0.02, bankroll=10_000)
    q = np.array([0.0, 0.0])
    signal = detector.evaluate(
        q=q, market_price=0.40, bayesian_probability=0.60, duration_hours=12.0
    )
    assert signal is not None
    assert signal.size_usd > 0


def test_no_signal_below_ev_threshold():
    detector = SignalDetector(b=100_000, ev_threshold=0.05)
    q = np.array([0.0, 0.0])
    signal = detector.evaluate(
        q=q, market_price=0.47, bayesian_probability=0.50, duration_hours=24.0
    )
    assert signal is None
