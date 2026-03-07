import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from data.feed import MarketFeed


@pytest.mark.asyncio
async def test_feed_instantiates():
    feed = MarketFeed(token_ids=["abc", "def"])
    assert feed.token_ids == ["abc", "def"]


@pytest.mark.asyncio
async def test_on_message_updates_orderbook():
    feed = MarketFeed(token_ids=["abc"])
    raw_msg = {
        "event_type": "book",
        "asset_id": "abc",
        "bids": [{"price": "0.48", "size": "100"}],
        "asks": [{"price": "0.52", "size": "200"}],
    }
    feed._handle_message(raw_msg)
    book = feed.get_orderbook("abc")
    assert book is not None
    assert abs(book.best_bid() - 0.48) < 1e-9


@pytest.mark.asyncio
async def test_unknown_event_type_does_not_crash():
    feed = MarketFeed(token_ids=["abc"])
    feed._handle_message({"event_type": "unknown", "asset_id": "abc"})
