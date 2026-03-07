"""
Polybot -- Polymarket Trading Bot
Usage:
  python main.py --dry-run          # Paper trade (no real orders)
  python main.py --scan             # Scan markets, print opportunities
  python main.py --live             # Live trading (requires API keys)
  python main.py --test             # Run test suite
"""
import asyncio
import argparse
import subprocess
import sys
from loguru import logger
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(description="Polybot -- Polymarket Trading Bot")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Paper trade (no real orders)")
    group.add_argument("--scan", action="store_true", help="Scan markets and print opportunities")
    group.add_argument("--live", action="store_true", help="Live trading (requires API keys)")
    group.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--bankroll", type=float, default=10_000.0, help="Trading bankroll in USD")
    return parser.parse_args()


async def run_scan(bankroll: float):
    from market.client import PolymarketClient
    from bot.scanner import MarketScanner

    client = PolymarketClient()
    scanner = MarketScanner(client=client, bankroll=bankroll)
    markets = client.get_markets(active_only=True)

    bayesian_probs = {m.get("token_id") or m.get("id"): 0.5 for m in markets}
    durations = {m.get("token_id") or m.get("id"): 24.0 for m in markets}

    signals = scanner.scan_all(markets, bayesian_probs, durations)

    table = Table(title="Market Opportunities")
    table.add_column("Token ID", style="cyan")
    table.add_column("Side", style="green")
    table.add_column("EV", style="magenta")
    table.add_column("Size USD", style="yellow")
    table.add_column("Market Price", style="white")

    for token_id, signal in signals:
        table.add_row(
            token_id[:20],
            signal.side,
            f"{signal.ev:.4f}",
            f"${signal.size_usd:.2f}",
            f"{signal.market_price:.4f}",
        )

    console.print(table)
    console.print(f"\n[bold]Found {len(signals)} opportunities[/bold]")


async def run_bot(dry_run: bool, bankroll: float):
    from market.client import PolymarketClient
    from bot.agent import TradingAgent

    client = PolymarketClient()
    agent = TradingAgent(client=client, bankroll=bankroll, dry_run=dry_run)
    mode = "DRY-RUN" if dry_run else "LIVE"
    console.print(f"[bold green]Polybot starting in {mode} mode[/bold green]")
    await agent.run()


def main():
    args = parse_args()

    if args.test:
        result = subprocess.run(["pytest", "tests/", "-v"], check=False)
        sys.exit(result.returncode)

    elif args.scan:
        asyncio.run(run_scan(args.bankroll))

    elif args.dry_run:
        asyncio.run(run_bot(dry_run=True, bankroll=args.bankroll))

    elif args.live:
        console.print("[bold red]WARNING: LIVE TRADING MODE[/bold red]")
        confirm = input("Type 'CONFIRM' to proceed with live trading: ")
        if confirm.strip() != "CONFIRM":
            console.print("Aborted.")
            sys.exit(0)
        asyncio.run(run_bot(dry_run=False, bankroll=args.bankroll))


if __name__ == "__main__":
    main()
