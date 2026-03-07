# Polybot — Claude Code Build Prompt & Project Memory

## STATUS: BUILD COMPLETE

---

## 🎯 MISSION

Build a fully autonomous Polymarket trading bot in Python that:
1. Connects to the Polymarket API (CLOB — Central Limit Order Book)
2. Detects pricing inefficiencies using LMSR math
3. Updates beliefs in real-time using Sequential Bayesian inference
4. Sizes positions using fractional Kelly with EV filtering
5. Executes trades automatically with risk controls

---

## 📐 CORE MATH (IMPLEMENT EXACTLY AS SPECIFIED)

### Module 1: LMSR Pricing Engine (`lmsr.py`)

The Logarithmic Market Scoring Rule cost function for n mutually exclusive outcomes with outstanding quantity vector **q** = (q1, q2, ..., qn):

```
C(q) = b · ln( Σ e^(qi/b) )          [equation 1 — THE KEY FORMULA]
```

Where:
- `b > 0` is the liquidity parameter controlling market depth
- Larger b → more liquidity, tighter spreads, higher max market maker loss
- Maximum market maker loss: `L_max = b · ln(n)`
- For binary markets (n=2) with b=100,000: L_max = 100,000 · ln(2) ≈ $69,315

**Price Function (Softmax)** — instantaneous price of outcome i:
```
p_i(q) = ∂C/∂qi = e^(qi/b) / Σ e^(qj/b)     [equation 3]
```

Critical properties: Σ p_i = 1 and p_i ∈ (0,1) ∀i
This is identical to the softmax function in neural network classifiers.

**Cost of a Trade** — to move outcome i from current quantity qi to qi + δ:
```
Cost = C(q1, ..., qi + δ, ..., qn) - C(q1, ..., qi, ..., qn)    [equation 4]
```

### Module 2: Bayesian Signal Processor (`bayesian.py`)

**Bayes' Theorem — Core Update Rule:**
```
P(H | D) = P(D | H) · P(H) / P(D) = (likelihood × prior) / evidence    [eq 1]
```

The traders who update fastest and most accurately win. Period.

**Sequential Bayesian Updating** — for a stream of data points D1, D2, ..., Dt:
```
P(H | D1, ..., Dt) ∝ P(H) · Π P(Dk | H)     [eq 2]
```

**In log-space (numerically stable) — ALWAYS USE THIS:**
```
log P(H | D) = log P(H) + Σ log P(Dk | H) - log Z    [eq 3]
```
Where Z is the normalizing constant.

### Module 3: Position Sizing (`kelly.py`)

**Expected Value** — for a position at price p with true probability p̂:
```
EV = p̂ · (1 - p) - (1 - p̂) · p = p̂ - p    [eq 4]
```

**⚠️ CRITICAL CONSTRAINT — ANNOTATED ON SOURCE DOCUMENT:**
> "NEVER full Kelly on 5min markets!"

- Use **fractional Kelly** (default: 0.25x Kelly) for all short-duration markets
- Markets < 1 hour duration: max 0.1x Kelly
- Markets 1–24 hours: max 0.25x Kelly  
- Markets > 24 hours: max 0.5x Kelly (still not full Kelly)

---

## 🏗️ PROJECT STRUCTURE TO BUILD

```
polybot/
├── CLAUDE.md                  # This file — project memory
├── README.md                  # User-facing docs
├── requirements.txt           # Dependencies
├── .env.example               # API key template (no real keys)
├── config.py                  # Configuration constants
│
├── core/
│   ├── __init__.py
│   ├── lmsr.py                # LMSR cost/price functions
│   ├── bayesian.py            # Bayesian belief updater
│   ├── kelly.py               # Position sizing
│   └── signals.py             # Inefficiency detection (entry conditions)
│
├── market/
│   ├── __init__.py
│   ├── client.py              # Polymarket CLOB API client
│   ├── orderbook.py           # Orderbook ingestion & parsing
│   └── executor.py            # Order execution layer
│
├── data/
│   ├── __init__.py
│   ├── feed.py                # Real-time data feed (websocket)
│   └── history.py             # Historical data fetcher
│
├── risk/
│   ├── __init__.py
│   └── manager.py             # Risk limits, position caps, drawdown stops
│
├── bot/
│   ├── __init__.py
│   ├── agent.py               # Main trading agent loop
│   └── scanner.py             # Market scanner (finds opportunities)
│
├── tests/
│   ├── test_lmsr.py
│   ├── test_bayesian.py
│   └── test_kelly.py
│
└── main.py                    # Entry point
```

---

## 🔧 IMPLEMENTATION INSTRUCTIONS FOR CLAUDE CODE

### Step 1: Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Build Order (implement in this exact sequence)

1. ✅ **`core/lmsr.py`** — Pure math, no dependencies. Build and test first.
2. ✅ **`core/kelly.py`** — Pure math, depends only on numpy.
3. ✅ **`core/bayesian.py`** — Pure math, numerically stable log-space.
4. ✅ **`core/signals.py`** — Combines LMSR + Bayesian to detect inefficiencies.
5. ✅ **`market/client.py`** — Polymarket CLOB API wrapper.
6. ✅ **`market/orderbook.py`** — Parse and maintain orderbook state.
7. ✅ **`data/feed.py`** — WebSocket connection for real-time data.
8. ✅ **`risk/manager.py`** — Hard limits BEFORE executor.
9. ✅ **`market/executor.py`** — Order placement (uses risk manager as gate).
10. ✅ **`bot/scanner.py`** — Scans markets for opportunities.
11. ✅ **`bot/agent.py`** — Main loop: data → signal → size → execute.
12. ✅ **`main.py`** — CLI entry point with dry-run mode.

### Step 3: Write tests as you go
Every core module must have a corresponding test in `/tests/`.

---

## 📋 DETAILED MODULE SPECS

### `core/lmsr.py`
```python
"""
LMSR Pricing Mechanism — implements equations 1-4 from QR-PM-2026-0041
"""
import numpy as np
from typing import List

def cost_function(q: np.ndarray, b: float) -> float:
    """C(q) = b * ln(sum(e^(qi/b))) — equation 1"""
    # Use logsumexp for numerical stability
    ...

def price_function(q: np.ndarray, b: float) -> np.ndarray:
    """p_i(q) = e^(qi/b) / sum(e^(qj/b)) — softmax, equation 3"""
    ...

def trade_cost(q: np.ndarray, b: float, outcome_idx: int, delta: float) -> float:
    """Cost of moving outcome i by delta — equation 4"""
    ...

def max_loss(b: float, n: int) -> float:
    """L_max = b * ln(n) — equation 2"""
    ...

def detect_inefficiency(market_price: float, lmsr_price: float, threshold: float = 0.02) -> float:
    """Returns signed inefficiency signal. Positive = market overpriced."""
    ...
```

### `core/bayesian.py`
```python
"""
Real-Time Bayesian Signal Processing — QR-PM-2026-0041 page 3
Update cycle target: < 828ms total (see latency table)
"""
import numpy as np

class BayesianBeliefUpdater:
    def __init__(self, prior: float):
        self.log_prior = np.log(prior)  # Always work in log-space
        self.log_posterior = self.log_prior
    
    def update(self, likelihood: float) -> float:
        """
        Sequential update: log P(H|D) = log P(H) + sum(log P(Dk|H)) - log Z
        Equation 3 — numerically stable log-space computation
        """
        ...
    
    def get_probability(self) -> float:
        """Convert log posterior to probability"""
        ...
    
    def reset(self, new_prior: float):
        """Reset beliefs (e.g., when market resolves)"""
        ...
```

### `core/kelly.py`
```python
"""
Position sizing via fractional Kelly criterion
EV = p_hat - p  (equation 4)

⚠️ NEVER FULL KELLY — fractional only (see source annotation)
"""

def expected_value(p_hat: float, p: float) -> float:
    """EV = p_hat * (1 - p) - (1 - p_hat) * p = p_hat - p"""
    return p_hat - p

def kelly_fraction(p_hat: float, p: float) -> float:
    """
    Full Kelly fraction for binary bet.
    f* = (p_hat - p) / (1 - p)  [when EV > 0]
    """
    ...

def fractional_kelly(p_hat: float, p: float, market_duration_hours: float) -> float:
    """
    Apply fractional Kelly based on market duration.
    
    ⚠️ CRITICAL: NEVER full Kelly on 5min markets (source annotation)
    < 1 hour:   0.10x Kelly
    1–24 hours: 0.25x Kelly  
    > 24 hours: 0.50x Kelly
    """
    ...

def position_size_usd(
    bankroll: float,
    p_hat: float, 
    p: float,
    market_duration_hours: float,
    max_position_pct: float = 0.05  # Hard cap: never risk > 5% bankroll per trade
) -> float:
    """Returns USD position size. Returns 0 if EV <= 0."""
    ...
```

### `market/client.py`
```python
"""
Polymarket CLOB API Client
Docs: https://docs.polymarket.com/
CLOB endpoint: https://clob.polymarket.com/
"""
import os
import requests
from py_clob_client.client import ClobClient

class PolymarketClient:
    BASE_URL = "https://clob.polymarket.com"
    
    def __init__(self):
        # Load from .env — NEVER hardcode keys
        self.api_key = os.getenv("POLY_API_KEY")
        self.private_key = os.getenv("POLY_PRIVATE_KEY")
        ...
    
    def get_markets(self, active_only=True) -> list:
        """Fetch available markets"""
        ...
    
    def get_orderbook(self, token_id: str) -> dict:
        """Fetch current orderbook for a token"""
        ...
    
    def place_order(self, token_id: str, side: str, price: float, size: float) -> dict:
        """Place a limit order. Returns order receipt."""
        ...
    
    def get_positions(self) -> list:
        """Get current open positions"""
        ...
```

### `risk/manager.py`
```python
"""
Risk Manager — gates ALL order execution
Hard limits that cannot be overridden by signal strength
"""

class RiskManager:
    def __init__(self, config):
        self.max_position_pct = config.MAX_POSITION_PCT   # e.g. 0.05 (5%)
        self.max_daily_loss = config.MAX_DAILY_LOSS_USD   # e.g. $500
        self.max_open_positions = config.MAX_OPEN_POSITIONS  # e.g. 10
        self.daily_pnl = 0.0
        self.open_positions = []
    
    def approve_trade(self, size_usd: float, ev: float, bankroll: float) -> tuple[bool, str]:
        """Returns (approved: bool, reason: str)"""
        # Check 1: EV must be positive
        # Check 2: Position size within limits
        # Check 3: Daily loss limit not breached
        # Check 4: Max open positions not exceeded
        ...
    
    def update_pnl(self, pnl: float):
        ...
```

---

## 🔑 CONFIGURATION (`config.py`)

```python
# Polymarket CLOB endpoints
CLOB_BASE_URL = "https://clob.polymarket.com"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"

# LMSR parameters
DEFAULT_B = 100_000  # Liquidity parameter

# Kelly / sizing
MAX_POSITION_PCT = 0.05        # Never risk more than 5% per trade
MAX_DAILY_LOSS_USD = 500       # Kill switch: halt if daily loss exceeds this
MAX_OPEN_POSITIONS = 10        # Portfolio concentration limit
MIN_EV_THRESHOLD = 0.02        # Minimum edge to trade (2%)
MIN_LIQUIDITY_USD = 1000       # Skip illiquid markets

# Timing
UPDATE_CYCLE_MS = 828          # Target: match production latency from paper
WEBSOCKET_RECONNECT_DELAY = 5  # seconds

# Kelly fractions by market duration
KELLY_UNDER_1HR = 0.10
KELLY_1_TO_24HR = 0.25
KELLY_OVER_24HR = 0.50
```

---

## 📦 REQUIREMENTS (`requirements.txt`)

```
# Polymarket
py-clob-client>=0.17.0
web3>=6.0.0

# Numerics
numpy>=1.26.0
scipy>=1.12.0

# Async / networking
aiohttp>=3.9.0
websockets>=12.0
asyncio

# Data
pandas>=2.0.0
python-dotenv>=1.0.0

# Utilities
loguru>=0.7.0
pydantic>=2.0.0
rich>=13.0.0    # Pretty CLI output

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## 🚀 MAIN ENTRY POINT (`main.py`)

```python
"""
Polybot — Polymarket Trading Bot
Usage:
  python main.py --dry-run          # Paper trade (no real orders)
  python main.py --scan             # Scan markets, print opportunities
  python main.py --live             # Live trading (requires API keys)
  python main.py --test             # Run test suite
"""
```

---

## ⚠️ WHAT REQUIRES USER INPUT (DO NOT BLOCK ON THESE — BUILD TO 80% FIRST)

1. **API Keys** — `POLY_API_KEY` and `POLY_PRIVATE_KEY` (Polygon wallet private key)
   - User must create at: https://polymarket.com → Settings → API
   - Add to `.env` file (template provided as `.env.example`)

2. **Wallet Funding** — Polymarket uses USDC on Polygon
   - User must deposit USDC to their Polymarket account

3. **Live Trading Approval** — Bot defaults to `--dry-run` mode
   - User must explicitly pass `--live` flag to place real orders

4. **Risk Parameter Tuning** — Defaults in `config.py` are conservative
   - User should review and adjust `MAX_DAILY_LOSS_USD` to their bankroll

---

## 📊 UPDATE CYCLE LATENCY TARGETS (from source paper)

| Component                    | Avg Target | p99 Target |
|------------------------------|-----------|------------|
| Data ingestion (API/WS)      | 120ms     | 340ms      |
| Bayesian posterior compute   | 15ms      | 28ms       |
| LMSR price comparison        | 3ms       | 8ms        |
| Order execution (CLOB)       | 690ms     | 1400ms     |
| **Total cycle**              | **828ms** | **1776ms** |

---

## 🤖 INSTRUCTIONS FOR CLAUDE CODE

**You are building a quantitative trading bot for Polymarket. Follow these steps in order:**

1. Read this entire CLAUDE.md file first
2. Create the directory structure exactly as specified
3. Implement modules in the order listed under "Build Order"
4. Write unit tests alongside each module
5. Start with `--dry-run` mode only — DO NOT implement live order execution until all math modules are tested and passing
6. Use `loguru` for all logging — structured, timestamped
7. Use `python-dotenv` for all secrets — never hardcode
8. All LMSR and Bayesian math must match the formulas in this file exactly
9. After building core math modules, write a `verify_math.py` script that cross-checks computed prices against known LMSR values
10. Update this CLAUDE.md with progress notes as you build

**When you finish each module, add a ✅ next to it in the Build Order above.**

**If you get stuck or need user input, stop, write clearly what is needed in the "BLOCKED ON" section below, and continue with the next unblocked module.**

---

## 🚧 BLOCKED ON (Claude Code: fill this in as needed)

*Nothing blocked — build in progress.*

---

## 📝 BUILD LOG (Claude Code: update as you go)

- [x] Project scaffolded
- [x] `core/lmsr.py` — implemented & tested (11 tests)
- [x] `core/kelly.py` — implemented & tested (13 tests)
- [x] `core/bayesian.py` — implemented & tested (9 tests)
- [x] `core/signals.py` — implemented & tested (5 tests)
- [x] `market/client.py` — implemented (3 tests)
- [x] `market/orderbook.py` — implemented (7 tests)
- [x] `data/feed.py` — websocket live (3 tests)
- [x] `risk/manager.py` — implemented & tested (7 tests)
- [x] `market/executor.py` — implemented (3 tests, dry-run only)
- [x] `bot/scanner.py` — implemented (3 tests)
- [x] `bot/agent.py` — main loop working (2 tests)
- [x] `main.py` — CLI working, dry-run tested
- [x] `verify_math.py` — all math cross-checks passing
- [x] End-to-end: 66 tests passing, math verified, CLI working
