import pytest
from market.orderbook import OrderBook, OrderBookLevel


def _sample_raw_book():
    return {
        "bids": [
            {"price": "0.48", "size": "500"},
            {"price": "0.47", "size": "1000"},
        ],
        "asks": [
            {"price": "0.52", "size": "300"},
            {"price": "0.53", "size": "800"},
        ],
    }


def test_parse_raw_orderbook():
    book = OrderBook.from_raw(_sample_raw_book())
    assert len(book.bids) == 2
    assert len(book.asks) == 2


def test_best_bid():
    book = OrderBook.from_raw(_sample_raw_book())
    assert abs(book.best_bid() - 0.48) < 1e-9


def test_best_ask():
    book = OrderBook.from_raw(_sample_raw_book())
    assert abs(book.best_ask() - 0.52) < 1e-9


def test_mid_price():
    book = OrderBook.from_raw(_sample_raw_book())
    expected_mid = (0.48 + 0.52) / 2
    assert abs(book.mid_price() - expected_mid) < 1e-9


def test_spread():
    book = OrderBook.from_raw(_sample_raw_book())
    assert abs(book.spread() - 0.04) < 1e-9


def test_empty_book_returns_none():
    book = OrderBook(bids=[], asks=[])
    assert book.best_bid() is None
    assert book.best_ask() is None
    assert book.mid_price() is None


def test_liquidity_at_price():
    """Total bid size at or above 0.47."""
    book = OrderBook.from_raw(_sample_raw_book())
    liq = book.bid_liquidity_usd(min_price=0.47)
    # 500 * 0.48 + 1000 * 0.47 = 240 + 470 = 710
    assert abs(liq - 710.0) < 1e-6
