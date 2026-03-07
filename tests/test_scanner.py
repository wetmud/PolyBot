import numpy as np
import pytest
from unittest.mock import MagicMock
from bot.scanner import MarketScanner
from market.orderbook import OrderBook


def make_scanner():
    client = MagicMock()
    return MarketScanner(client=client, bankroll=10_000)


def _make_book(bid, ask):
    raw = {
        "bids": [{"price": str(bid), "size": "5000"}],
        "asks": [{"price": str(ask), "size": "5000"}],
    }
    return OrderBook.from_raw(raw)


def test_scanner_finds_opportunity():
    scanner = make_scanner()
    # mid=0.45, bayesian says 0.60 -> strong BUY signal
    book = _make_book(bid=0.44, ask=0.46)
    signal = scanner.evaluate_market(
        token_id="abc",
        book=book,
        bayesian_probability=0.60,
        duration_hours=12.0,
    )
    assert signal is not None
    assert signal.side == "BUY"


def test_scanner_returns_none_when_no_edge():
    scanner = make_scanner()
    book = _make_book(bid=0.49, ask=0.51)
    signal = scanner.evaluate_market(
        token_id="abc",
        book=book,
        bayesian_probability=0.50,
        duration_hours=12.0,
    )
    assert signal is None


def test_scanner_skips_illiquid_market():
    scanner = make_scanner()
    raw = {
        "bids": [{"price": "0.44", "size": "1"}],  # tiny liquidity
        "asks": [{"price": "0.56", "size": "1"}],
    }
    book = OrderBook.from_raw(raw)
    signal = scanner.evaluate_market(
        token_id="abc",
        book=book,
        bayesian_probability=0.60,
        duration_hours=12.0,
    )
    assert signal is None
