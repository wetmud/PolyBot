"""
Position sizing via fractional Kelly criterion.
EV = p_hat - p  (equation 4 from CLAUDE.md spec)

NEVER FULL KELLY -- fractional only.
"""
import config


def expected_value(p_hat: float, p: float) -> float:
    """EV = p_hat * (1 - p) - (1 - p_hat) * p = p_hat - p"""
    return p_hat - p


def kelly_fraction(p_hat: float, p: float) -> float:
    """
    Full Kelly fraction for a binary bet.
    f* = (p_hat - p) / (1 - p)  when EV > 0, else 0.
    """
    ev = expected_value(p_hat, p)
    if ev <= 0:
        return 0.0
    return ev / (1 - p)


def fractional_kelly(p_hat: float, p: float, market_duration_hours: float) -> float:
    """
    Apply fractional Kelly based on market duration.
    NEVER full Kelly (source annotation).
    < 1 hour:   0.10x Kelly
    1-24 hours: 0.25x Kelly
    > 24 hours: 0.50x Kelly
    """
    full_k = kelly_fraction(p_hat, p)
    if full_k == 0.0:
        return 0.0

    if market_duration_hours < 1.0:
        fraction = config.KELLY_UNDER_1HR
    elif market_duration_hours <= 24.0:
        fraction = config.KELLY_1_TO_24HR
    else:
        fraction = config.KELLY_OVER_24HR

    return full_k * fraction


def position_size_usd(
    bankroll: float,
    p_hat: float,
    p: float,
    market_duration_hours: float,
    max_position_pct: float = 0.05,
) -> float:
    """
    Returns USD position size. Returns 0 if EV <= 0.
    Hard cap: never risk more than max_position_pct of bankroll.
    """
    if expected_value(p_hat, p) <= 0:
        return 0.0
    frac = fractional_kelly(p_hat, p, market_duration_hours)
    raw_size = bankroll * frac
    cap = bankroll * max_position_pct
    return min(raw_size, cap)
