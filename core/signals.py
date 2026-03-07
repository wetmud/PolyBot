"""
Inefficiency detection: combines LMSR pricing + Bayesian probability
to generate trading signals.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional

import config
from core.lmsr import price_function, detect_inefficiency
from core.kelly import expected_value, position_size_usd


@dataclass
class Signal:
    side: str          # "BUY" or "SELL"
    ev: float          # Expected value of the trade
    size_usd: float    # Recommended position size in USD
    market_price: float
    fair_price: float  # Bayesian estimate


class SignalDetector:
    def __init__(
        self,
        b: float = config.DEFAULT_B,
        ev_threshold: float = config.MIN_EV_THRESHOLD,
        bankroll: float = 10_000.0,
    ):
        self.b = b
        self.ev_threshold = ev_threshold
        self.bankroll = bankroll

    def evaluate(
        self,
        q: np.ndarray,
        market_price: float,
        bayesian_probability: float,
        duration_hours: float,
    ) -> Optional[Signal]:
        """
        Compare market_price to bayesian_probability.
        Returns a Signal if edge exceeds ev_threshold, else None.
        """
        ev = expected_value(p_hat=bayesian_probability, p=market_price)

        if abs(ev) < self.ev_threshold:
            return None

        side = "BUY" if ev > 0 else "SELL"
        # For SELL, p_hat is the complement probability
        p_hat_for_sizing = bayesian_probability if side == "BUY" else (1 - bayesian_probability)
        p_for_sizing = market_price if side == "BUY" else (1 - market_price)

        size = position_size_usd(
            bankroll=self.bankroll,
            p_hat=p_hat_for_sizing,
            p=p_for_sizing,
            market_duration_hours=duration_hours,
            max_position_pct=config.MAX_POSITION_PCT,
        )

        if size <= 0:
            return None

        return Signal(
            side=side,
            ev=abs(ev),
            size_usd=size,
            market_price=market_price,
            fair_price=bayesian_probability,
        )
