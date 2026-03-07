"""
Real-time WebSocket feed for Polymarket CLOB market data.
Reconnects automatically on disconnect.
"""
import asyncio
import json
from typing import Callable, Optional
from loguru import logger
import websockets

import config
from market.orderbook import OrderBook


class MarketFeed:
    WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def __init__(self, token_ids: list[str], on_update: Optional[Callable] = None):
        self.token_ids = token_ids
        self.on_update = on_update  # optional callback for new orderbook data
        self._books: dict[str, OrderBook] = {}
        self._running = False

    def get_orderbook(self, token_id: str) -> Optional[OrderBook]:
        return self._books.get(token_id)

    def _handle_message(self, msg: dict):
        event_type = msg.get("event_type")
        asset_id = msg.get("asset_id")
        if event_type == "book" and asset_id:
            book = OrderBook.from_raw(msg)
            self._books[asset_id] = book
            if self.on_update:
                self.on_update(asset_id, book)
        # Other event types (trades, ticks) ignored for now

    async def _subscribe(self, ws):
        payload = {
            "auth": {},
            "type": "Market",
            "assets_ids": self.token_ids,
        }
        await ws.send(json.dumps(payload))
        logger.info(f"Subscribed to {len(self.token_ids)} markets")

    async def run(self):
        """Connect and listen; reconnect on disconnect."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self.WS_URL, ping_interval=20) as ws:
                    await self._subscribe(ws)
                    async for raw in ws:
                        msg = json.loads(raw)
                        if isinstance(msg, list):
                            for m in msg:
                                self._handle_message(m)
                        else:
                            self._handle_message(msg)
            except Exception as e:
                logger.warning(f"WebSocket error: {e}. Reconnecting in {config.WEBSOCKET_RECONNECT_DELAY}s")
                await asyncio.sleep(config.WEBSOCKET_RECONNECT_DELAY)

    def stop(self):
        self._running = False
