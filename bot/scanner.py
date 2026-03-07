"""
Market scanner: finds pricing opportunities across Polymarket markets.
"""
import numpy as np
from typing import Optional
from loguru import logger

import config
from core.signals import SignalDetector, Signal
from core.bayesian import BayesianBeliefUpdater
from market.orderbook import OrderBook


class MarketScanner:
    def __init__(self, client, bankroll: float = 10_000.0):
        self.client = client
        self.bankroll = bankroll
        self._detector = SignalDetector(
            b=config.DEFAULT_B,
            ev_threshold=config.MIN_EV_THRESHOLD,
            bankroll=bankroll,
        )

    def evaluate_market(
        self,
        token_id: str,
        book: OrderBook,
        bayesian_probability: float,
        duration_hours: float,
    ) -> Optional[Signal]:
        """
        Evaluate a single market for a trading opportunity.
        Returns Signal if edge found, None otherwise.
        """
        mid = book.mid_price()
        if mid is None:
            return None

        # Skip illiquid markets
        liq = book.bid_liquidity_usd(min_price=0.0)
        if liq < config.MIN_LIQUIDITY_USD:
            logger.debug(f"Skipping {token_id}: liquidity ${liq:.0f} < ${config.MIN_LIQUIDITY_USD}")
            return None

        q = np.array([0.0, 0.0])  # neutral LMSR state (no position taken yet)
        signal = self._detector.evaluate(
            q=q,
            market_price=mid,
            bayesian_probability=bayesian_probability,
            duration_hours=duration_hours,
        )
        if signal:
            logger.info(f"Signal found on {token_id}: {signal.side} ev={signal.ev:.4f}")
        return signal

    def scan_all(self, markets: list, bayesian_probs: dict, durations: dict) -> list[tuple]:
        """
        Scan a list of markets. Returns list of (token_id, Signal) pairs.
        markets: list of market dicts with 'token_id' key.
        bayesian_probs: {token_id: float}
        durations: {token_id: hours_float}
        """
        results = []
        for market in markets:
            token_id = market.get("token_id") or market.get("id")
            if not token_id:
                continue
            try:
                raw_book = self.client.get_orderbook(token_id)
                book = OrderBook.from_raw(raw_book)
                p_hat = bayesian_probs.get(token_id, 0.5)
                hours = durations.get(token_id, 24.0)
                signal = self.evaluate_market(token_id, book, p_hat, hours)
                if signal:
                    results.append((token_id, signal))
            except Exception as e:
                logger.warning(f"Error scanning {token_id}: {e}")
        return results
