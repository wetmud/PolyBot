# PolyBot - Polymarket Trading Bot

An autonomous trading bot for [Polymarket](https://polymarket.com) prediction markets. It finds mispriced markets, calculates how much to bet, and executes trades automatically.

## What Does It Actually Do?

PolyBot works in 4 steps every cycle (~1 second):

1. **Scans markets** - Pulls live orderbook data from Polymarket's API
2. **Detects mispricings** - Compares market prices to its own probability estimates using LMSR math (the same math Polymarket uses internally)
3. **Sizes bets** - Uses the Kelly Criterion to figure out how much to wager (never goes "full Kelly" - always uses conservative fractions to avoid blowing up)
4. **Executes trades** - Places orders through Polymarket's CLOB (Central Limit Order Book), but only after passing all risk checks

### Safety Features

- **Dry-run mode by default** - No real money moves unless you explicitly say so
- **Risk manager gates every trade** - Max 5% of bankroll per trade, $500 daily loss limit, max 10 open positions
- **Fractional Kelly only** - The bot never bets full Kelly (which is notoriously aggressive). Short-duration markets get extra conservative sizing
- **Live mode requires typing CONFIRM** - Can't accidentally start live trading

## Project Structure

```
PolyBot/
├── core/               # The math engine
│   ├── lmsr.py         # Market pricing math (cost functions, fair prices)
│   ├── bayesian.py     # Belief updating (how confident are we?)
│   ├── kelly.py        # Bet sizing (how much should we wager?)
│   └── signals.py      # Combines the above into BUY/SELL signals
│
├── market/             # Polymarket connectivity
│   ├── client.py       # API wrapper (fetches markets, places orders)
│   ├── orderbook.py    # Parses bid/ask data
│   └── executor.py     # Executes trades (with risk gate)
│
├── data/
│   └── feed.py         # Real-time WebSocket market data
│
├── risk/
│   └── manager.py      # Hard limits on every trade
│
├── bot/
│   ├── scanner.py      # Scans all markets for opportunities
│   └── agent.py        # Main loop that ties everything together
│
├── main.py             # CLI entry point (start here)
├── config.py           # All tunable parameters
├── verify_math.py      # Cross-checks the math is correct
└── tests/              # 66 unit tests
```

## Quick Start

### 1. Install Python

You need Python 3.11 or newer. Check with:

```bash
python3 --version
```

### 2. Set Up the Project

```bash
cd /path/to/PolyBot

# Create a virtual environment (keeps dependencies isolated)
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 3. Run the Tests

Make sure everything works:

```bash
python main.py --test
```

You should see `66 passed`. If so, the math and logic are all verified.

### 4. Get Your Polymarket API Keys

You need two things: an **API Key** and a **Private Key** (your Polygon wallet key).

**Step-by-step:**

1. Go to [polymarket.com](https://polymarket.com) and create an account (or log in)
2. You'll need a funded Polygon wallet - Polymarket uses USDC on the Polygon network
3. To get API access:
   - Go to your Polymarket profile/settings
   - Look for API or Developer settings
   - Generate an API key
4. Your **private key** is the private key of the Polygon wallet you connected to Polymarket
   - If you use MetaMask: Settings > Security & Privacy > Reveal Secret Recovery Phrase (this is your wallet key)
   - **NEVER share this with anyone or commit it to git**

### 5. Configure Your Keys

```bash
# Copy the example env file
cp .env.example .env

# Edit it with your keys
nano .env   # or open .env in any text editor
```

Your `.env` file should look like:

```
POLY_API_KEY=your_actual_api_key_here
POLY_PRIVATE_KEY=your_actual_private_key_here
```

**Important:** The `.env` file is in `.gitignore` so it won't accidentally get committed.

### 6. Run the Bot

```bash
# Scan markets for opportunities (read-only, no trades)
python main.py --scan

# Paper trade - simulates trades without spending real money
python main.py --dry-run

# Paper trade with a specific bankroll
python main.py --dry-run --bankroll 5000

# Live trading (REAL MONEY - be careful!)
python main.py --live
```

**Start with `--scan` and `--dry-run` first.** Get comfortable with the output before even thinking about `--live`.

## Configuring Risk Parameters

Edit `config.py` to adjust:

| Parameter | Default | What It Does |
|-----------|---------|--------------|
| `MAX_POSITION_PCT` | 5% | Max % of bankroll per trade |
| `MAX_DAILY_LOSS_USD` | $500 | Kill switch - stops trading if you lose this much in a day |
| `MAX_OPEN_POSITIONS` | 10 | Max simultaneous bets |
| `MIN_EV_THRESHOLD` | 2% | Minimum edge required to trade |
| `MIN_LIQUIDITY_USD` | $1000 | Skip markets with less liquidity than this |

## How the Math Works (Plain English)

- **LMSR** (Logarithmic Market Scoring Rule): This is the formula Polymarket uses to price outcomes. We use it to calculate what a "fair" price should be, then compare it to the actual market price.

- **Bayesian Updating**: As new information comes in, the bot updates its beliefs about how likely each outcome is. It does this in "log-space" so the numbers don't break with extreme probabilities.

- **Kelly Criterion**: Once we know our edge (how mispriced something is), Kelly tells us the mathematically optimal bet size. But full Kelly is too aggressive, so we use fractions:
  - Markets ending in < 1 hour: bet 10% of Kelly
  - Markets ending in 1-24 hours: bet 25% of Kelly
  - Markets ending in > 24 hours: bet 50% of Kelly

## FAQ

**Q: Will I make money?**
A: No guarantees. This bot finds mathematical mispricings, but prediction markets are efficient and edges are small. Start with paper trading.

**Q: Is my private key safe?**
A: It's stored locally in your `.env` file, which is gitignored. Never commit it, never share it.

**Q: What's USDC?**
A: A stablecoin pegged to $1 USD. Polymarket runs on the Polygon network using USDC. You'll need to bridge USDC to Polygon to fund your account.

**Q: Can I lose more than my bankroll?**
A: No. Prediction market positions are bounded - you can only lose what you bet. Plus the risk manager caps each trade at 5% of your bankroll.

**Q: The bot isn't finding any signals?**
A: That's normal. The default 2% EV threshold means the bot only trades when it finds a meaningful edge. Efficient markets don't have mispricings very often.
