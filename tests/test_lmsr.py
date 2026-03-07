import numpy as np
import pytest
from core.lmsr import cost_function, price_function, trade_cost, max_loss, detect_inefficiency


def test_cost_function_symmetric():
    """Equal quantities -> symmetric cost."""
    q = np.array([0.0, 0.0])
    b = 100.0
    # C([0,0], b=100) = b * ln(2) ~ 69.315
    result = cost_function(q, b)
    assert abs(result - b * np.log(2)) < 1e-9


def test_cost_function_scalar():
    q = np.array([100.0, 0.0])
    b = 100.0
    result = cost_function(q, b)
    assert isinstance(result, float)
    assert result > 0


def test_price_function_sums_to_one():
    q = np.array([50.0, 150.0, 100.0])
    b = 200.0
    prices = price_function(q, b)
    assert abs(prices.sum() - 1.0) < 1e-12


def test_price_function_softmax_properties():
    q = np.array([0.0, 0.0])
    b = 100.0
    prices = price_function(q, b)
    # Equal quantities -> equal prices = 0.5
    assert abs(prices[0] - 0.5) < 1e-12
    assert abs(prices[1] - 0.5) < 1e-12


def test_price_function_ordering():
    """Higher quantity -> higher price."""
    q = np.array([200.0, 0.0])
    b = 100.0
    prices = price_function(q, b)
    assert prices[0] > prices[1]


def test_trade_cost_positive_buy():
    """Buying shares increases cost."""
    q = np.array([0.0, 0.0])
    b = 100.0
    cost = trade_cost(q, b, outcome_idx=0, delta=10.0)
    assert cost > 0


def test_trade_cost_zero_delta():
    q = np.array([50.0, 50.0])
    b = 100.0
    cost = trade_cost(q, b, outcome_idx=0, delta=0.0)
    assert abs(cost) < 1e-12


def test_max_loss_binary():
    """L_max = b * ln(n). For n=2, b=100_000: ~ 69315."""
    result = max_loss(100_000, 2)
    assert abs(result - 100_000 * np.log(2)) < 1e-6


def test_detect_inefficiency_overpriced():
    """Market price above LMSR -> positive signal."""
    signal = detect_inefficiency(market_price=0.60, lmsr_price=0.50, threshold=0.02)
    assert signal > 0


def test_detect_inefficiency_underpriced():
    signal = detect_inefficiency(market_price=0.40, lmsr_price=0.50, threshold=0.02)
    assert signal < 0


def test_detect_inefficiency_within_threshold():
    """Small gap -> zero signal (no edge)."""
    signal = detect_inefficiency(market_price=0.505, lmsr_price=0.50, threshold=0.02)
    assert signal == 0.0
