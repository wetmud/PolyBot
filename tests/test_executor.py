import pytest
from unittest.mock import MagicMock
from market.executor import OrderExecutor
from core.signals import Signal
from risk.manager import RiskManager


def make_executor(dry_run=True):
    client = MagicMock()
    rm = RiskManager(max_position_pct=0.05, max_daily_loss=500.0, max_open_positions=10)
    return OrderExecutor(client=client, risk_manager=rm, dry_run=dry_run), client, rm


def make_signal(ev=0.05, size=100.0):
    return Signal(side="BUY", ev=ev, size_usd=size, market_price=0.45, fair_price=0.55)


def test_dry_run_does_not_call_client():
    executor, client, _ = make_executor(dry_run=True)
    result = executor.execute(
        token_id="abc", signal=make_signal(), bankroll=10_000
    )
    assert result["dry_run"] is True
    client.place_order.assert_not_called()


def test_risk_rejected_trade_returns_rejected():
    executor, client, rm = make_executor(dry_run=False)
    rm.daily_pnl = -600.0  # blow daily limit
    result = executor.execute(token_id="abc", signal=make_signal(), bankroll=10_000)
    assert result["status"] == "rejected"
    client.place_order.assert_not_called()


def test_live_mode_calls_client(monkeypatch):
    executor, client, _ = make_executor(dry_run=False)
    client.place_order.return_value = {"order_id": "xyz", "status": "open"}
    result = executor.execute(
        token_id="abc", signal=make_signal(ev=0.05, size=100.0), bankroll=10_000
    )
    client.place_order.assert_called_once()
    assert result["status"] in ("open", "filled", "dry_run", "rejected")
