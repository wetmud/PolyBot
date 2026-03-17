# PolyBot

Autonomous algorithmic trading bot for [Polymarket](https://polymarket.com) prediction markets — detects mispriced outcomes and executes positions using LMSR math, Bayesian inference, and fractional Kelly sizing.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

---

## What it does

PolyBot runs a continuous scan-and-trade loop against Polymarket's CLOB (Central Limit Order Book):

1. **Scans markets** — pulls live orderbook data from the Polymarket API and WebSocket feed
2. **Detects mispricings** — compares current market prices to fair-value estimates derived from the LMSR cost function
3. **Updates beliefs** — applies sequential Bayesian inference in log-space as new price data arrives
4. **Sizes positions** — uses fractional Kelly criterion scaled by market duration (shorter markets get more conservative sizing)
5. **Executes trades** — every order passes through a risk manager before hitting the CLOB; dry-run mode by default

### Safety controls

- **Dry-run by default** — no real orders placed unless you pass `--live`
- **Live mode requires typing `CONFIRM`** — can't accidentally start real trading
- **Risk manager gates every trade** — checks EV, position size, daily loss limit, and open position count before approving any order
- **Fractional Kelly only** — never full Kelly; short-duration markets get extra conservative multipliers

---

## Project structure

```
PolyBot/
├── core/
│   ├── lmsr.py         # LMSR cost/price functions (fair value math)
│   ├── bayesian.py     # Sequential Bayesian belief updater (log-space)
│   ├── kelly.py        # Fractional Kelly position sizing
│   └── signals.py      # Combines LMSR + Bayesian into BUY/SELL signals
├── market/
│   ├── client.py       # Polymarket CLOB API wrapper
│   ├── orderbook.py    # Orderbook parsing and state
│   └── executor.py     # Order execution (gated by risk manager)
├── data/
│   └── feed.py         # Real-time WebSocket market data
├── risk/
│   └── manager.py      # Hard limits: position caps, daily loss kill switch
├── bot/
│   ├── scanner.py      # Scans all markets for opportunities
│   └── agent.py        # Main trading loop
├── tests/              # 66 unit tests
├── main.py             # CLI entry point
├── config.py           # All tunable parameters
└── verify_math.py      # Cross-checks LMSR and Kelly math
```

---

## Setup

### Requirements

- Python 3.11+
- A funded Polymarket account with USDC on Polygon
- Polymarket API key and your Polygon wallet private key

### Install

```bash
git clone https://github.com/wetmud/PolyBot.git
cd PolyBot

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Verify the math

Run the test suite before doing anything else:

```bash
python main.py --test
```

You should see `66 passed`. If any tests fail, do not proceed.

### Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```
POLY_API_KEY=your_api_key_here
POLY_PRIVATE_KEY=your_polygon_wallet_private_key_here
```

The `.env` file is gitignored. Never commit it. Never share your private key.

---

## Usage

```bash
# Scan markets for mispricings — read-only, no orders placed
python main.py --scan

# Paper trade — full bot loop, simulated orders only
python main.py --dry-run

# Paper trade with a specific starting bankroll
python main.py --dry-run --bankroll 5000

# Live trading — REAL MONEY, requires typing CONFIRM at the prompt
python main.py --live --bankroll 5000
```

Start with `--scan`, then `--dry-run`. Only move to `--live` once you understand the output and are comfortable with the risk parameters.

---

## How it works

**LMSR (Logarithmic Market Scoring Rule)**
Polymarket prices outcomes using the LMSR cost function `C(q) = b · ln(Σ e^(qi/b))`. PolyBot uses the same formula to compute a fair-value price for each outcome, then compares it to the current market price to find the inefficiency signal.

**Bayesian belief updating**
As new orderbook data arrives, the bot updates its probability estimates using sequential Bayesian inference in log-space: `log P(H|D) = log P(H) + Σ log P(Dk|H) - log Z`. Log-space arithmetic prevents numerical underflow with extreme probabilities.

**Fractional Kelly sizing**
Once an edge is found, Kelly gives the mathematically optimal bet fraction. PolyBot always applies a conservative multiplier based on how much time is left in the market:

| Market duration | Kelly multiplier |
|-----------------|-----------------|
| < 1 hour        | 10% of Kelly    |
| 1–24 hours      | 25% of Kelly    |
| > 24 hours      | 50% of Kelly    |

Full Kelly is never used.

**Update cycle target:** ~828ms total (120ms data ingestion, 15ms Bayesian update, 3ms LMSR comparison, 690ms CLOB execution).

---

## Configuration

All parameters live in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_POSITION_PCT` | `0.05` | Max fraction of bankroll per trade (5%) |
| `MAX_DAILY_LOSS_USD` | `500` | Daily loss kill switch — halts trading if breached |
| `MAX_OPEN_POSITIONS` | `10` | Max simultaneous open positions |
| `MIN_EV_THRESHOLD` | `0.02` | Minimum edge required to trade (2%) |
| `MIN_LIQUIDITY_USD` | `1000` | Skip markets with less than this in liquidity |
| `KELLY_UNDER_1HR` | `0.10` | Kelly fraction for sub-1-hour markets |
| `KELLY_1_TO_24HR` | `0.25` | Kelly fraction for 1–24 hour markets |
| `KELLY_OVER_24HR` | `0.50` | Kelly fraction for markets > 24 hours |

Adjust `MAX_DAILY_LOSS_USD` to a value you are genuinely comfortable losing in a single day before running live.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POLY_API_KEY` | Yes (live only) | Polymarket API key from your account settings |
| `POLY_PRIVATE_KEY` | Yes (live only) | Private key of the Polygon wallet connected to Polymarket |

Neither variable is required for `--scan` or `--dry-run` mode. For live trading, both must be present in `.env`.

---

## Disclaimer

**This is experimental software. Use it at your own risk.**

- PolyBot places real orders with real money when run in `--live` mode. You can lose your entire bankroll.
- Past performance in dry-run mode does not predict live trading results. Prediction markets are adversarial; edges are small and can disappear.
- This software is not financial advice. Nothing in this codebase or documentation constitutes a recommendation to trade.
- The author makes no guarantees about profitability, correctness, or fitness for any particular purpose.
- Algorithmic trading on prediction markets may be subject to terms-of-service restrictions depending on your jurisdiction and platform. It is your responsibility to ensure you are operating within applicable rules.

---

## License

MIT
