"""
Order execution layer. Risk manager is the gate — no order bypasses it.
Default: dry_run=True (paper trading). Live requires explicit opt-in.
"""
from loguru import logger
from core.signals import Signal
from risk.manager import RiskManager


class OrderExecutor:
    def __init__(self, client, risk_manager: RiskManager, dry_run: bool = True):
        self.client = client
        self.risk = risk_manager
        self.dry_run = dry_run

    def execute(self, token_id: str, signal: Signal, bankroll: float) -> dict:
        """
        Gate through risk manager, then execute (or simulate).
        Returns a result dict with status and details.
        """
        approved, reason = self.risk.approve_trade(
            size_usd=signal.size_usd, ev=signal.ev, bankroll=bankroll
        )
        if not approved:
            logger.warning(f"Trade rejected: {reason}")
            return {"status": "rejected", "reason": reason}

        if self.dry_run:
            logger.info(
                f"[DRY RUN] {signal.side} {signal.size_usd:.2f} USD on {token_id} "
                f"@ {signal.market_price:.4f} (fair={signal.fair_price:.4f}, ev={signal.ev:.4f})"
            )
            return {
                "status": "dry_run",
                "dry_run": True,
                "token_id": token_id,
                "side": signal.side,
                "size_usd": signal.size_usd,
                "price": signal.market_price,
            }

        try:
            receipt = self.client.place_order(
                token_id=token_id,
                side=signal.side,
                price=signal.market_price,
                size=signal.size_usd,
            )
            logger.info(f"Order executed: {receipt}")
            return receipt
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            return {"status": "error", "error": str(e)}
