import pytest
from risk.manager import RiskManager


def make_rm(**kwargs):
    defaults = dict(
        max_position_pct=0.05,
        max_daily_loss=500.0,
        max_open_positions=10,
    )
    defaults.update(kwargs)
    return RiskManager(**defaults)


def test_approve_valid_trade():
    rm = make_rm()
    approved, reason = rm.approve_trade(size_usd=100.0, ev=0.05, bankroll=10_000)
    assert approved is True


def test_reject_negative_ev():
    rm = make_rm()
    approved, reason = rm.approve_trade(size_usd=100.0, ev=-0.01, bankroll=10_000)
    assert approved is False
    assert "EV" in reason


def test_reject_oversized_position():
    rm = make_rm(max_position_pct=0.05)
    # 600 > 5% of 10_000 (= 500)
    approved, reason = rm.approve_trade(size_usd=600.0, ev=0.05, bankroll=10_000)
    assert approved is False
    assert "position" in reason.lower()


def test_reject_when_daily_loss_exceeded():
    rm = make_rm(max_daily_loss=500.0)
    rm.update_pnl(-501.0)
    approved, reason = rm.approve_trade(size_usd=100.0, ev=0.05, bankroll=10_000)
    assert approved is False
    assert "daily" in reason.lower()


def test_reject_when_max_positions_reached():
    rm = make_rm(max_open_positions=2)
    rm.open_positions = ["pos1", "pos2"]
    approved, reason = rm.approve_trade(size_usd=100.0, ev=0.05, bankroll=10_000)
    assert approved is False
    assert "positions" in reason.lower()


def test_pnl_updates_correctly():
    rm = make_rm()
    rm.update_pnl(-200.0)
    rm.update_pnl(50.0)
    assert abs(rm.daily_pnl - (-150.0)) < 1e-9


def test_reset_daily_resets_pnl():
    rm = make_rm()
    rm.update_pnl(-300.0)
    rm.reset_daily()
    assert rm.daily_pnl == 0.0
