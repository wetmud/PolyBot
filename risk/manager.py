"""
Risk Manager — gates ALL order execution.
Hard limits that cannot be overridden by signal strength.
"""
from loguru import logger


class RiskManager:
    def __init__(
        self,
        max_position_pct: float,
        max_daily_loss: float,
        max_open_positions: int,
    ):
        self.max_position_pct = max_position_pct
        self.max_daily_loss = max_daily_loss
        self.max_open_positions = max_open_positions
        self.daily_pnl: float = 0.0
        self.open_positions: list = []

    def approve_trade(self, size_usd: float, ev: float, bankroll: float) -> tuple[bool, str]:
        """Returns (approved, reason). All checks must pass."""
        if ev <= 0:
            return False, f"EV non-positive: {ev:.4f}"

        max_size = bankroll * self.max_position_pct
        if size_usd > max_size:
            return False, f"Position size ${size_usd:.2f} exceeds max ${max_size:.2f}"

        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit breached: ${self.daily_pnl:.2f}"

        if len(self.open_positions) >= self.max_open_positions:
            return False, f"Max open positions reached: {len(self.open_positions)}"

        return True, "approved"

    def update_pnl(self, pnl: float):
        self.daily_pnl += pnl
        logger.debug(f"Daily PnL updated: ${self.daily_pnl:.2f}")

    def reset_daily(self):
        """Call at start of each trading day."""
        self.daily_pnl = 0.0
        logger.info("Daily PnL reset")
