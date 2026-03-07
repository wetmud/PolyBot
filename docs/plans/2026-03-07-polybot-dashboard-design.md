# PolyBot Dashboard — Design Document

**Date:** 2026-03-07
**Status:** Approved

## Overview

A browser-based dashboard for PolyBot that replaces the CLI as the primary interface. Served by FastAPI, updated in real-time via WebSocket. Single command to launch: `python main.py --dashboard`.

## Goals

1. Let a non-technical user start/stop/monitor the bot without touching the terminal
2. Show live market opportunities, positions, and risk status
3. Allow editing configuration (bankroll, risk limits) through the UI
4. Keep it simple — single HTML file, no build step, no Node.js

## Architecture

```
dashboard/
├── __init__.py
├── app.py          # FastAPI application, lifespan, static file serving
├── routes.py       # REST endpoints: /api/status, /api/config, /api/start, /api/stop
├── ws.py           # WebSocket manager: broadcasts bot state to connected clients
└── static/
    └── index.html  # Single-page dashboard (Tailwind CDN + vanilla JS)
```

### How it connects to the existing bot

- `TradingAgent` runs as an asyncio background task inside FastAPI's lifespan
- `RiskManager` state is read directly (daily P&L, open positions, limits)
- `MarketScanner` results are captured each cycle and broadcast via WebSocket
- No data duplication — dashboard reads from the same objects the bot uses

### Data Flow

```
Browser ←WebSocket← FastAPI ← TradingAgent.run_cycle()
Browser →REST API→  FastAPI → start/stop/config changes
```

## Dashboard Sections

### 1. Header / Status Bar
- Bot mode: Idle / Scanning / Dry-Run / Live
- Connection status indicator (green dot / red dot)
- Uptime counter
- Last cycle timestamp

### 2. Bot Controls
- **Start Scan** button — read-only market scanning
- **Start Dry-Run** button — paper trading with configurable bankroll
- **Start Live** button — requires confirmation modal ("Type CONFIRM to proceed")
- **Stop** button — halts current mode
- Bankroll input field (editable when stopped)

### 3. Market Opportunities Table
- Columns: Market, Side (BUY/SELL), EV, Size USD, Market Price, Fair Price
- Auto-updates each cycle via WebSocket
- Sorted by EV descending
- Color-coded: green for BUY, red for SELL

### 4. Risk Monitor
- Daily P&L display (green/red)
- Progress bars for:
  - Daily loss limit usage (e.g., $120 / $500)
  - Open positions count (e.g., 3 / 10)
  - Largest position as % of bankroll
- Warning states when approaching limits

### 5. Activity Feed
- Scrolling list of recent events:
  - Signals detected
  - Trades executed (or would-be-executed in dry-run)
  - Risk rejections with reason
- Timestamps for each entry
- Max 100 entries, newest first

### 6. Configuration Panel
- Editable fields for:
  - `MAX_POSITION_PCT`
  - `MAX_DAILY_LOSS_USD`
  - `MAX_OPEN_POSITIONS`
  - `MIN_EV_THRESHOLD`
  - `MIN_LIQUIDITY_USD`
- Save button applies changes to running bot
- Reset to defaults button

## API Endpoints

### REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Bot mode, uptime, last cycle, connection health |
| GET | `/api/config` | Current configuration values |
| POST | `/api/config` | Update configuration |
| POST | `/api/start` | Start bot in specified mode (scan/dry-run/live) |
| POST | `/api/stop` | Stop the bot |
| GET | `/api/positions` | Current open positions |
| GET | `/api/history` | Recent activity/trade history |

### WebSocket

| Path | Description |
|------|-------------|
| `/ws` | Real-time updates: signals, risk state, activity events |

WebSocket messages are JSON with a `type` field:
- `signals` — new market opportunities from latest scan
- `risk` — updated risk state (daily P&L, positions)
- `activity` — new trade/event
- `status` — bot mode/state change

## Tech Decisions

- **Tailwind CSS via CDN** — no build step, just a `<script>` tag
- **Vanilla JS** — no React/Vue/framework. Dashboard is simple enough for plain JS
- **FastAPI** — async, pairs with existing asyncio bot, built-in WebSocket support
- **uvicorn** — ASGI server, included with FastAPI
- **webbrowser module** — auto-open dashboard in browser on launch

## Dependencies to Add

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
```

## Entry Point

Add `--dashboard` flag to `main.py`:
```
python main.py --dashboard              # Launch dashboard (bot starts idle)
python main.py --dashboard --port 8080  # Custom port
```

Dashboard serves on `http://localhost:8501` by default.
