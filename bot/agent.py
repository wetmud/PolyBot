"""
Main trading agent loop.
Orchestrates: data -> Bayesian update -> signal -> risk -> execute.
"""
import asyncio
from datetime import datetime, timezone
from loguru import logger
from typing import Optional

import config
from market.client import PolymarketClient
from market.orderbook import OrderBook
from market.executor import OrderExecutor
from risk.manager import RiskManager
from bot.scanner import MarketScanner
from core.bayesian import BayesianBeliefUpdater


class TradingAgent:
    def __init__(self, client: PolymarketClient, bankroll: float, dry_run: bool = True):
        self.client = client
        self.bankroll = bankroll
        self.dry_run = dry_run

        self._risk = RiskManager(
            max_position_pct=config.MAX_POSITION_PCT,
            max_daily_loss=config.MAX_DAILY_LOSS_USD,
            max_open_positions=config.MAX_OPEN_POSITIONS,
        )
        self._executor = OrderExecutor(client=client, risk_manager=self._risk, dry_run=dry_run)
        self._scanner = MarketScanner(client=client, bankroll=bankroll)

        # Bayesian belief per token_id; initialized to 0.5 (uniform prior)
        self._bayesian_updaters: dict[str, BayesianBeliefUpdater] = {}
        self._bayesian_probs: dict[str, float] = {}

    def _get_updater(self, token_id: str) -> BayesianBeliefUpdater:
        if token_id not in self._bayesian_updaters:
            self._bayesian_updaters[token_id] = BayesianBeliefUpdater(prior=0.5)
        return self._bayesian_updaters[token_id]

    def _market_duration_hours(self, market: dict) -> float:
        """Parse market end date and return hours remaining."""
        try:
            end_str = market.get("end_date_iso") or market.get("end_date")
            if end_str:
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                delta = (end_dt - now).total_seconds() / 3600.0
                return max(delta, 0.1)
        except Exception:
            pass
        return 24.0  # default

    async def run_cycle(self) -> list:
        """Single update cycle: fetch markets, scan, execute. Returns list of results."""
        results = []
        try:
            markets = self.client.get_markets(active_only=True)
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            return results

        bayesian_probs = {
            m.get("token_id") or m.get("id"): self._bayesian_probs.get(
                m.get("token_id") or m.get("id"), 0.5
            )
            for m in markets
        }
        durations = {
            m.get("token_id") or m.get("id"): self._market_duration_hours(m)
            for m in markets
        }

        signals = self._scanner.scan_all(markets, bayesian_probs, durations)

        for token_id, signal in signals:
            result = self._executor.execute(
                token_id=token_id, signal=signal, bankroll=self.bankroll
            )
            results.append({"token_id": token_id, "signal": signal, "result": result})

        return results

    async def run(self, cycle_interval_ms: int = config.UPDATE_CYCLE_MS):
        """Main loop. Runs indefinitely until stopped."""
        logger.info(f"Agent starting — dry_run={self.dry_run}, bankroll=${self.bankroll:,.0f}")
        self._risk.reset_daily()
        while True:
            results = await self.run_cycle()
            if results:
                logger.info(f"Cycle complete: {len(results)} signals processed")
            await asyncio.sleep(cycle_interval_ms / 1000.0)
