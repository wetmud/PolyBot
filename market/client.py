"""
Polymarket CLOB API Client.
Docs: https://docs.polymarket.com/
CLOB endpoint: https://clob.polymarket.com/
"""
import os
import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class PolymarketClient:
    BASE_URL = "https://clob.polymarket.com"

    def __init__(self):
        self.api_key = os.getenv("POLY_API_KEY")
        self.private_key = os.getenv("POLY_PRIVATE_KEY")
        if not self.api_key or not self.private_key:
            logger.warning("POLY_API_KEY or POLY_PRIVATE_KEY not set — running in read-only mode")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def get_markets(self, active_only: bool = True) -> list:
        """Fetch available markets from the CLOB."""
        url = f"{self.BASE_URL}/markets"
        params = {"active": "true"} if active_only else {}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", data) if isinstance(data, dict) else data

    def get_orderbook(self, token_id: str) -> dict:
        """Fetch current orderbook for a token."""
        url = f"{self.BASE_URL}/book"
        resp = requests.get(url, params={"token_id": token_id}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def place_order(self, token_id: str, side: str, price: float, size: float) -> dict:
        """
        Place a limit order. Returns order receipt.
        Raises RuntimeError if API keys not configured.
        """
        if not self.api_key or not self.private_key:
            raise RuntimeError("API keys not configured — cannot place orders")
        url = f"{self.BASE_URL}/order"
        payload = {
            "token_id": token_id,
            "side": side.upper(),
            "price": price,
            "size": size,
            "type": "GTC",
        }
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        logger.info(f"Order placed: {side} {size} @ {price} on {token_id}")
        return resp.json()

    def get_positions(self) -> list:
        """Get current open positions."""
        if not self.api_key:
            return []
        url = f"{self.BASE_URL}/positions"
        resp = requests.get(url, headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
