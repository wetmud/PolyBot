import pytest
from unittest.mock import patch, MagicMock
from market.client import PolymarketClient


def test_client_instantiates_without_keys(monkeypatch):
    """Client should not crash if env vars are missing — just store None."""
    monkeypatch.delenv("POLY_API_KEY", raising=False)
    monkeypatch.delenv("POLY_PRIVATE_KEY", raising=False)
    client = PolymarketClient()
    assert client.api_key is None
    assert client.private_key is None


def test_get_markets_returns_list(monkeypatch):
    monkeypatch.setenv("POLY_API_KEY", "fake_key")
    monkeypatch.setenv("POLY_PRIVATE_KEY", "fake_pk")
    client = PolymarketClient()

    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "abc", "active": True}]}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response):
        markets = client.get_markets()
    assert isinstance(markets, list)


def test_place_order_raises_without_keys():
    client = PolymarketClient()
    with pytest.raises(RuntimeError, match="API keys not configured"):
        client.place_order(token_id="abc", side="BUY", price=0.5, size=100.0)
