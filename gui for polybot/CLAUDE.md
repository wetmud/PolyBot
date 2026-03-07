# PolyBot Dashboard — GUI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a browser-based dashboard so the user can start/stop/monitor PolyBot without touching the terminal.

**Architecture:** FastAPI backend serves a single-page HTML dashboard. The existing `TradingAgent` runs as an asyncio background task inside FastAPI. Real-time updates flow to the browser via WebSocket. REST endpoints handle start/stop/config. Zero changes to core math modules.

**Tech Stack:** FastAPI, uvicorn, Tailwind CSS (CDN), vanilla JavaScript, WebSocket

---

## Design Overview

```
┌──────────────────────────────────────────────────────────────┐
│ POLYBOT DASHBOARD           [Idle] [●] Connected    00:00:00 │
├──────────────────────────────────────────────────────────────┤
│ Bankroll: [$10,000]    [Scan] [Dry Run] [Live] [Stop]        │
├───────────────────────────────────┬──────────────────────────┤
│ Market Opportunities              │ Risk Monitor             │
│ ┌───────────────────────────────┐ │ Daily P&L: $0.00        │
│ │ Token  Side  EV   Size   Px  │ │ ████░░░░░░ $0/$500      │
│ │ abc..  BUY  4.2%  $50  .45  │ │                          │
│ │ def..  SELL 3.1%  $30  .62  │ │ Positions: 0/10          │
│ └───────────────────────────────┘ │ ██░░░░░░░░ 0/10         │
├───────────────────────────────────┴──────────────────────────┤
│ Activity Feed                                                │
│ 12:00:01 Signal: BUY abc @ 0.45 (EV: 4.2%)                  │
│ 12:00:01 Trade: DRY RUN BUY $50.00 on abc                   │
│ 11:59:30 Cycle complete: 1 signal processed                  │
├──────────────────────────────────────────────────────────────┤
│ Settings (collapsible)                                       │
│ Max Position %: [5]  Max Daily Loss: [$500]  Min EV: [0.02]  │
└──────────────────────────────────────────────────────────────┘
```

- Dark theme (slate-900 bg, slate-800 cards)
- Green (#22c55e) = BUY / profit, Red (#ef4444) = SELL / loss
- Monospace numbers, smooth update animations
- Mobile-responsive (Tailwind breakpoints)

---

## New Files to Create

```
dashboard/
├── __init__.py
├── state.py           # BotState shared state container
├── app.py             # FastAPI app, lifespan, static serving
├── routes.py          # REST API endpoints
├── ws.py              # WebSocket connection manager
└── static/
    └── index.html     # Single-page dashboard (Tailwind + vanilla JS)
```

## Existing Files to Modify

```
bot/agent.py           # Add _state, _running flag, stop() method
main.py                # Add --dashboard flag
requirements.txt       # Add fastapi, uvicorn
```

---

## REST API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Bot mode, uptime, cycle count, bankroll |
| GET | `/api/config` | Current risk/trading config values |
| POST | `/api/config` | Update config values at runtime |
| POST | `/api/start` | Start bot — body: `{"mode": "scan\|dry_run\|live"}` |
| POST | `/api/stop` | Stop the bot |
| GET | `/api/signals` | Latest scan results |
| GET | `/api/risk` | Daily P&L, open positions, limit usage |
| GET | `/api/activity` | Recent activity log (last 100 events) |

## WebSocket

| Path | Description |
|------|-------------|
| `/ws` | Streams JSON messages with `type` field |

Message types: `status`, `signals`, `risk`, `activity`

---

## Task 0: Dependencies & Scaffolding

**Files:**
- Modify: `requirements.txt`
- Create: `dashboard/__init__.py`
- Create: `dashboard/static/` (directory)

**Step 1: Add dependencies to requirements.txt**

Append to `requirements.txt`:
```
# Dashboard
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
```

**Step 2: Create dashboard package**

```bash
mkdir -p dashboard/static
touch dashboard/__init__.py
```

**Step 3: Install new deps**

```bash
pip install fastapi uvicorn[standard]
```

**Step 4: Commit**

```bash
git add dashboard/__init__.py requirements.txt
git commit -m "chore: add dashboard scaffolding and fastapi deps"
```

---

## Task 1: BotState — Shared State Container

**Files:**
- Create: `dashboard/state.py`
- Create: `tests/test_state.py`

**Step 1: Write the failing test**

`tests/test_state.py`:
```python
"""Tests for BotState shared state container."""
import pytest
from dashboard.state import BotState


def test_initial_state():
    state = BotState()
    assert state.mode == "idle"
    assert state.is_running is False
    assert state.bankroll == 10_000.0
    assert state.cycle_count == 0
    assert state.signals == []
    assert state.activity == []


def test_add_activity_inserts_at_front():
    state = BotState()
    state.add_activity({"type": "test", "message": "first"})
    state.add_activity({"type": "test", "message": "second"})
    assert len(state.activity) == 2
    assert state.activity[0]["message"] == "second"
    assert "timestamp" in state.activity[0]


def test_activity_capped_at_100():
    state = BotState()
    for i in range(120):
        state.add_activity({"type": "test", "i": i})
    assert len(state.activity) == 100
    assert state.activity[0]["i"] == 119  # newest


def test_to_dict():
    state = BotState()
    state.mode = "dry_run"
    state.bankroll = 5000.0
    d = state.to_dict()
    assert d["mode"] == "dry_run"
    assert d["bankroll"] == 5000.0
    assert isinstance(d, dict)


def test_update_from_risk():
    state = BotState()
    state.update_risk(daily_pnl=-50.0, open_positions=["pos1", "pos2"])
    assert state.daily_pnl == -50.0
    assert state.open_positions == ["pos1", "pos2"]


def test_update_signals():
    state = BotState()
    sigs = [{"token_id": "abc", "side": "BUY", "ev": 0.04}]
    state.signals = sigs
    assert state.signals[0]["token_id"] == "abc"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_state.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.state'`

**Step 3: Write implementation**

`dashboard/state.py`:
```python
"""
BotState — shared state container between TradingAgent and Dashboard.
The agent writes to it each cycle; the dashboard reads via REST/WebSocket.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BotState:
    mode: str = "idle"  # idle, scanning, dry_run, live
    is_running: bool = False
    bankroll: float = 10_000.0
    cycle_count: int = 0
    last_cycle_time: Optional[str] = None
    started_at: Optional[str] = None

    # Latest scan results (list of signal dicts)
    signals: list = field(default_factory=list)

    # Risk state
    daily_pnl: float = 0.0
    open_positions: list = field(default_factory=list)

    # Activity log (newest first, capped at 100)
    activity: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def add_activity(self, event: dict):
        entry = {**event, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.activity.insert(0, entry)
        self.activity = self.activity[:100]

    def update_risk(self, daily_pnl: float, open_positions: list):
        self.daily_pnl = daily_pnl
        self.open_positions = list(open_positions)
```

**Step 4: Run tests**

```bash
pytest tests/test_state.py -v
```
Expected: 6 passed

**Step 5: Commit**

```bash
git add dashboard/state.py tests/test_state.py
git commit -m "feat: add BotState shared state container"
```

---

## Task 2: Modify TradingAgent for Dashboard Integration

**Files:**
- Modify: `bot/agent.py`
- Create: `tests/test_agent_dashboard.py`

**Step 1: Write the failing test**

`tests/test_agent_dashboard.py`:
```python
"""Tests for TradingAgent dashboard integration."""
import pytest
from unittest.mock import MagicMock
from bot.agent import TradingAgent
from dashboard.state import BotState


def test_agent_accepts_state():
    client = MagicMock()
    state = BotState()
    agent = TradingAgent(client=client, bankroll=10_000, dry_run=True, state=state)
    assert agent._state is state


def test_agent_works_without_state():
    client = MagicMock()
    agent = TradingAgent(client=client, bankroll=10_000, dry_run=True)
    assert agent._state is None


def test_agent_stop():
    client = MagicMock()
    agent = TradingAgent(client=client, bankroll=10_000)
    agent._running = True
    agent.stop()
    assert agent._running is False


@pytest.mark.asyncio
async def test_run_cycle_updates_state():
    client = MagicMock()
    client.get_markets.return_value = []
    state = BotState()
    agent = TradingAgent(client=client, bankroll=10_000, state=state)
    await agent.run_cycle()
    assert state.cycle_count == 1
    assert state.last_cycle_time is not None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_agent_dashboard.py -v
```
Expected: FAIL — `TypeError: TradingAgent.__init__() got an unexpected keyword argument 'state'`

**Step 3: Modify bot/agent.py**

Changes to `TradingAgent.__init__`:
```python
def __init__(self, client: PolymarketClient, bankroll: float, dry_run: bool = True, state=None):
    self.client = client
    self.bankroll = bankroll
    self.dry_run = dry_run
    self._state = state  # Optional BotState for dashboard
    self._running = False

    # ... rest unchanged ...
```

Changes to `run_cycle` — append at end before `return results`:
```python
    # Update dashboard state if attached
    if self._state:
        self._state.cycle_count += 1
        self._state.last_cycle_time = datetime.now(timezone.utc).isoformat()
        self._state.signals = [
            {
                "token_id": tid,
                "side": sig.side,
                "ev": round(sig.ev, 4),
                "size_usd": round(sig.size_usd, 2),
                "market_price": round(sig.market_price, 4),
                "fair_price": round(sig.fair_price, 4),
            }
            for tid, sig in signals
        ]
        self._state.update_risk(
            daily_pnl=self._risk.daily_pnl,
            open_positions=list(self._risk.open_positions),
        )
        for item in results:
            self._state.add_activity({
                "type": "trade",
                "token_id": item["token_id"],
                "side": item["signal"].side,
                "ev": round(item["signal"].ev, 4),
                "size_usd": round(item["signal"].size_usd, 2),
                "status": item["result"].get("status", "unknown"),
            })

    return results
```

Changes to `run`:
```python
async def run(self, cycle_interval_ms: int = config.UPDATE_CYCLE_MS):
    logger.info(f"Agent starting — dry_run={self.dry_run}, bankroll=${self.bankroll:,.0f}")
    self._risk.reset_daily()
    self._running = True
    while self._running:
        results = await self.run_cycle()
        if results:
            logger.info(f"Cycle complete: {len(results)} signals processed")
        await asyncio.sleep(cycle_interval_ms / 1000.0)
```

Add `stop` method:
```python
def stop(self):
    """Gracefully stop the agent loop."""
    self._running = False
    logger.info("Agent stop requested")
```

**Step 4: Run all tests**

```bash
pytest tests/test_agent_dashboard.py tests/test_agent.py -v
```
Expected: All pass (new + existing)

**Step 5: Commit**

```bash
git add bot/agent.py tests/test_agent_dashboard.py
git commit -m "feat: add dashboard state integration to TradingAgent"
```

---

## Task 3: WebSocket Manager

**Files:**
- Create: `dashboard/ws.py`
- Create: `tests/test_ws.py`

**Step 1: Write the failing test**

`tests/test_ws.py`:
```python
"""Tests for WebSocket connection manager."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from dashboard.ws import ConnectionManager


@pytest.mark.asyncio
async def test_connect_adds_to_active():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect(ws)
    assert len(mgr.active_connections) == 1
    ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_removes():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect(ws)
    mgr.disconnect(ws)
    assert len(mgr.active_connections) == 0


@pytest.mark.asyncio
async def test_broadcast_sends_to_all():
    mgr = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await mgr.connect(ws1)
    await mgr.connect(ws2)
    await mgr.broadcast({"type": "test"})
    ws1.send_json.assert_awaited_once_with({"type": "test"})
    ws2.send_json.assert_awaited_once_with({"type": "test"})


@pytest.mark.asyncio
async def test_broadcast_handles_dead_connection():
    mgr = ConnectionManager()
    ws_good = AsyncMock()
    ws_dead = AsyncMock()
    ws_dead.send_json.side_effect = Exception("disconnected")
    await mgr.connect(ws_good)
    await mgr.connect(ws_dead)
    await mgr.broadcast({"type": "test"})
    # Should not raise, dead connection removed
    assert ws_good in mgr.active_connections
    assert ws_dead not in mgr.active_connections
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_ws.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

`dashboard/ws.py`:
```python
"""WebSocket connection manager — broadcasts bot state to dashboard clients."""
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.active_connections.remove(conn)
```

**Step 4: Run tests**

```bash
pytest tests/test_ws.py -v
```
Expected: 4 passed

**Step 5: Commit**

```bash
git add dashboard/ws.py tests/test_ws.py
git commit -m "feat: add WebSocket connection manager"
```

---

## Task 4: REST API Routes

**Files:**
- Create: `dashboard/routes.py`
- Create: `tests/test_routes.py`

**Step 1: Write the failing test**

`tests/test_routes.py`:
```python
"""Tests for dashboard REST API routes."""
import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app
from dashboard.state import BotState


@pytest.fixture
def client():
    app = create_app(bankroll=10_000.0)
    return TestClient(app)


def test_get_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "idle"
    assert data["is_running"] is False


def test_get_config(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "max_position_pct" in data
    assert "max_daily_loss_usd" in data


def test_update_config(client):
    resp = client.post("/api/config", json={"max_daily_loss_usd": 250})
    assert resp.status_code == 200
    resp2 = client.get("/api/config")
    assert resp2.json()["max_daily_loss_usd"] == 250


def test_get_signals_empty(client):
    resp = client.get("/api/signals")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_risk(client):
    resp = client.get("/api/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert "daily_pnl" in data
    assert "open_positions" in data


def test_get_activity_empty(client):
    resp = client.get("/api/activity")
    assert resp.status_code == 200
    assert resp.json() == []


def test_start_scan(client):
    resp = client.post("/api/start", json={"mode": "scan"})
    # Will fail without real API keys, but route should exist
    assert resp.status_code in (200, 500)


def test_stop_when_idle(client):
    resp = client.post("/api/stop")
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_routes.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.app'`

**Step 3: Write implementation**

`dashboard/routes.py`:
```python
"""REST API routes for the PolyBot dashboard."""
import asyncio
from fastapi import APIRouter, Request
from loguru import logger

import config

router = APIRouter(prefix="/api")


@router.get("/status")
async def get_status(request: Request):
    state = request.app.state.bot_state
    return {
        "mode": state.mode,
        "is_running": state.is_running,
        "bankroll": state.bankroll,
        "cycle_count": state.cycle_count,
        "last_cycle_time": state.last_cycle_time,
        "started_at": state.started_at,
    }


@router.get("/config")
async def get_config(request: Request):
    return {
        "max_position_pct": config.MAX_POSITION_PCT,
        "max_daily_loss_usd": config.MAX_DAILY_LOSS_USD,
        "max_open_positions": config.MAX_OPEN_POSITIONS,
        "min_ev_threshold": config.MIN_EV_THRESHOLD,
        "min_liquidity_usd": config.MIN_LIQUIDITY_USD,
        "kelly_under_1hr": config.KELLY_UNDER_1HR,
        "kelly_1_to_24hr": config.KELLY_1_TO_24HR,
        "kelly_over_24hr": config.KELLY_OVER_24HR,
    }


@router.post("/config")
async def update_config(request: Request):
    body = await request.json()
    allowed = {
        "max_position_pct", "max_daily_loss_usd", "max_open_positions",
        "min_ev_threshold", "min_liquidity_usd",
    }
    for key, value in body.items():
        if key in allowed:
            setattr(config, key.upper(), value)
            logger.info(f"Config updated: {key} = {value}")
    return {"status": "ok", "updated": list(body.keys())}


@router.get("/signals")
async def get_signals(request: Request):
    return request.app.state.bot_state.signals


@router.get("/risk")
async def get_risk(request: Request):
    state = request.app.state.bot_state
    return {
        "daily_pnl": state.daily_pnl,
        "open_positions": state.open_positions,
        "max_daily_loss": config.MAX_DAILY_LOSS_USD,
        "max_open_positions": config.MAX_OPEN_POSITIONS,
    }


@router.get("/activity")
async def get_activity(request: Request):
    return request.app.state.bot_state.activity


@router.post("/start")
async def start_bot(request: Request):
    body = await request.json()
    mode = body.get("mode", "scan")
    state = request.app.state.bot_state

    if state.is_running:
        return {"status": "error", "message": "Bot is already running"}

    from datetime import datetime, timezone
    from market.client import PolymarketClient
    from bot.agent import TradingAgent

    client = PolymarketClient()
    dry_run = mode != "live"
    state.mode = mode.replace("-", "_")
    state.bankroll = state.bankroll
    state.is_running = True
    state.started_at = datetime.now(timezone.utc).isoformat()

    agent = TradingAgent(
        client=client, bankroll=state.bankroll, dry_run=dry_run, state=state
    )
    request.app.state.agent = agent

    # Run agent in background
    task = asyncio.create_task(agent.run())
    request.app.state.agent_task = task

    logger.info(f"Bot started in {mode} mode")
    return {"status": "ok", "mode": mode}


@router.post("/stop")
async def stop_bot(request: Request):
    state = request.app.state.bot_state
    agent = getattr(request.app.state, "agent", None)

    if agent:
        agent.stop()

    task = getattr(request.app.state, "agent_task", None)
    if task and not task.done():
        task.cancel()

    state.is_running = False
    state.mode = "idle"
    state.add_activity({"type": "system", "message": "Bot stopped"})
    request.app.state.agent = None
    request.app.state.agent_task = None

    return {"status": "ok"}
```

**Step 4: This depends on Task 5 (app.py) — implement both, then test together.**

---

## Task 5: FastAPI App

**Files:**
- Create: `dashboard/app.py`

**Step 1: Write implementation**

`dashboard/app.py`:
```python
"""FastAPI application for the PolyBot dashboard."""
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from dashboard.state import BotState
from dashboard.ws import ConnectionManager
from dashboard.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Dashboard starting up")
    yield
    # Shutdown: stop agent if running
    agent = getattr(app.state, "agent", None)
    if agent:
        agent.stop()
    logger.info("Dashboard shutting down")


def create_app(bankroll: float = 10_000.0) -> FastAPI:
    app = FastAPI(title="PolyBot Dashboard", lifespan=lifespan)

    # Shared state
    app.state.bot_state = BotState(bankroll=bankroll)
    app.state.ws_manager = ConnectionManager()
    app.state.agent = None
    app.state.agent_task = None

    # Routes
    app.include_router(router)

    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Serve index.html at root
    @app.get("/")
    async def root():
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "PolyBot Dashboard — place index.html in dashboard/static/"}

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        mgr = app.state.ws_manager
        await mgr.connect(websocket)
        try:
            while True:
                # Send state every second
                state = app.state.bot_state
                await websocket.send_json({
                    "type": "state",
                    "data": state.to_dict(),
                })
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            mgr.disconnect(websocket)
        except Exception:
            mgr.disconnect(websocket)

    return app
```

**Step 2: Run route tests**

```bash
pytest tests/test_routes.py -v
```
Expected: 8 passed

**Step 3: Commit**

```bash
git add dashboard/app.py dashboard/routes.py tests/test_routes.py
git commit -m "feat: add FastAPI app with REST routes and WebSocket"
```

---

## Task 6: Frontend Dashboard

> **Use the `frontend-design` skill** to create `dashboard/static/index.html`.

**Files:**
- Create: `dashboard/static/index.html`

**Requirements for the frontend-design skill:**
- Single HTML file with Tailwind CSS via CDN
- Dark theme (slate-900 background)
- No framework — vanilla JS only
- Connects to `/ws` WebSocket on page load
- Calls REST endpoints for start/stop/config
- Sections: Header/Status, Controls, Market Opportunities table, Risk Monitor, Activity Feed, Settings panel
- Color scheme: green (#22c55e) for BUY/profit, red (#ef4444) for SELL/loss
- Responsive layout using Tailwind grid

**Key JS behaviors:**
```javascript
// WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws`);
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "state") updateDashboard(msg.data);
};

// Start bot
async function startBot(mode) {
    if (mode === "live") {
        if (!confirm("WARNING: This will place REAL orders. Continue?")) return;
    }
    await fetch("/api/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode}),
    });
}

// Stop bot
async function stopBot() {
    await fetch("/api/stop", {method: "POST"});
}

// Update dashboard from WebSocket state
function updateDashboard(state) {
    // Update status bar (mode, cycle count, uptime)
    // Update signals table
    // Update risk gauges
    // Update activity feed
}
```

**Step 1: Implement using frontend-design skill**

The HTML should be a complete, self-contained file. No external dependencies except Tailwind CDN.

**Step 2: Manual test**

```bash
cd /path/to/polybot
python -c "
import uvicorn
from dashboard.app import create_app
app = create_app()
uvicorn.run(app, host='0.0.0.0', port=8501)
"
```
Open http://localhost:8501 in browser. Verify layout renders correctly.

**Step 3: Commit**

```bash
git add dashboard/static/index.html
git commit -m "feat: add dashboard frontend"
```

---

## Task 7: main.py — Add --dashboard Flag

**Files:**
- Modify: `main.py`

**Step 1: Add --dashboard to arg parser and handler**

In `parse_args()`, add to the mutually exclusive group:
```python
group.add_argument("--dashboard", action="store_true", help="Launch web dashboard")
```

Add port argument:
```python
parser.add_argument("--port", type=int, default=8501, help="Dashboard port (default: 8501)")
```

In `main()`, add handler before `elif args.scan`:
```python
elif args.dashboard:
    import webbrowser
    import uvicorn
    from dashboard.app import create_app

    app = create_app(bankroll=args.bankroll)
    console.print(f"[bold green]PolyBot Dashboard starting at http://localhost:{args.port}[/bold green]")
    webbrowser.open(f"http://localhost:{args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
```

**Step 2: Test manually**

```bash
python main.py --dashboard
```
Expected: browser opens, dashboard loads.

```bash
python main.py --dashboard --port 9000 --bankroll 5000
```
Expected: custom port and bankroll work.

**Step 3: Verify existing modes still work**

```bash
python main.py --test
```
Expected: All tests pass (66 original + new dashboard tests)

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add --dashboard flag to CLI"
```

---

## Task 8: Integration Testing & Final Verification

**Step 1: Run full test suite**

```bash
pytest tests/ -v
```
Expected: All tests pass (original 66 + ~18 new dashboard tests)

**Step 2: Manual end-to-end test**

```bash
python main.py --dashboard --bankroll 10000
```

In browser:
1. Verify dashboard loads with dark theme
2. Click "Scan" — verify status changes to "scanning"
3. Click "Stop" — verify returns to "idle"
4. Click "Dry Run" — verify cycle count increments
5. Verify signals table updates (if markets available)
6. Verify activity feed populates
7. Verify risk monitor shows P&L and position count
8. Edit config values, verify they persist
9. Resize browser — verify responsive layout

**Step 3: Update CLAUDE.md build log**

Add to build log:
```
- [x] `dashboard/state.py` — BotState container (6 tests)
- [x] `dashboard/ws.py` — WebSocket manager (4 tests)
- [x] `dashboard/routes.py` — REST API (8 tests)
- [x] `dashboard/app.py` — FastAPI app
- [x] `dashboard/static/index.html` — Frontend dashboard
- [x] `main.py` updated with --dashboard flag
```

**Step 4: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with dashboard build log"
```

---

## Summary

| Task | What | New Tests |
|------|------|-----------|
| 0 | Dependencies & scaffolding | — |
| 1 | BotState shared state | 6 |
| 2 | TradingAgent dashboard hooks | 4 |
| 3 | WebSocket manager | 4 |
| 4 | REST API routes | 8 |
| 5 | FastAPI app setup | — |
| 6 | Frontend HTML (frontend-design skill) | — |
| 7 | main.py --dashboard | — |
| 8 | Integration test & docs | — |

**Total new tests: ~22**
**Total files created: 7**
**Total files modified: 3**
**New dependencies: 2 (fastapi, uvicorn)**
