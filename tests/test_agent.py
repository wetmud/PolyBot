import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from bot.agent import TradingAgent


def make_agent(dry_run=True):
    client = MagicMock()
    client.get_markets.return_value = [{"token_id": "abc", "end_date_iso": "2026-03-10T00:00:00Z"}]
    client.get_orderbook.return_value = {
        "bids": [{"price": "0.44", "size": "5000"}],
        "asks": [{"price": "0.46", "size": "5000"}],
    }
    return TradingAgent(client=client, bankroll=10_000, dry_run=dry_run)


def test_agent_instantiates():
    agent = make_agent()
    assert agent.dry_run is True


@pytest.mark.asyncio
async def test_agent_single_cycle_dry_run():
    agent = make_agent(dry_run=True)
    # Override bayesian probs to create a signal
    agent._bayesian_probs = {"abc": 0.65}
    results = await agent.run_cycle()
    assert isinstance(results, list)
