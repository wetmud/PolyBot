"""
Orderbook ingestion and parsing for Polymarket CLOB data.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class OrderBook:
    bids: list[OrderBookLevel]  # sorted descending by price
    asks: list[OrderBookLevel]  # sorted ascending by price

    @classmethod
    def from_raw(cls, raw: dict) -> "OrderBook":
        bids = sorted(
            [OrderBookLevel(float(l["price"]), float(l["size"])) for l in raw.get("bids", [])],
            key=lambda x: x.price,
            reverse=True,
        )
        asks = sorted(
            [OrderBookLevel(float(l["price"]), float(l["size"])) for l in raw.get("asks", [])],
            key=lambda x: x.price,
        )
        return cls(bids=bids, asks=asks)

    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None

    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is None or ba is None:
            return None
        return (bb + ba) / 2.0

    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is None or ba is None:
            return None
        return ba - bb

    def bid_liquidity_usd(self, min_price: float = 0.0) -> float:
        """Total USD value of bids at or above min_price."""
        return sum(lvl.price * lvl.size for lvl in self.bids if lvl.price >= min_price)
