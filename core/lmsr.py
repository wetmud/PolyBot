"""
LMSR Pricing Mechanism
Implements equations 1-4 from CLAUDE.md spec.
"""
import numpy as np
from scipy.special import logsumexp


def cost_function(q: np.ndarray, b: float) -> float:
    """C(q) = b * ln(sum(e^(qi/b))) — equation 1. Uses logsumexp for stability."""
    return float(b * logsumexp(q / b))


def price_function(q: np.ndarray, b: float) -> np.ndarray:
    """p_i(q) = softmax(q/b) — equation 3."""
    shifted = q / b - np.max(q / b)  # numerical stability
    exp_vals = np.exp(shifted)
    return exp_vals / exp_vals.sum()


def trade_cost(q: np.ndarray, b: float, outcome_idx: int, delta: float) -> float:
    """Cost of moving outcome i by delta — equation 4."""
    q_new = q.copy()
    q_new[outcome_idx] += delta
    return cost_function(q_new, b) - cost_function(q, b)


def max_loss(b: float, n: int) -> float:
    """L_max = b * ln(n) — equation 2."""
    return b * np.log(n)


def detect_inefficiency(market_price: float, lmsr_price: float, threshold: float = 0.02) -> float:
    """
    Returns signed inefficiency signal.
    Positive = market overpriced (sell opportunity).
    Negative = market underpriced (buy opportunity).
    Zero = within threshold, no edge.
    """
    diff = market_price - lmsr_price
    if abs(diff) < threshold:
        return 0.0
    return diff
