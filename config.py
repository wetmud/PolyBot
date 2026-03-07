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
