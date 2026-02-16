from datetime import datetime
from pathlib import Path

# === FUND CONSTANTS ===
HURDLE_RATE_ANNUAL = 0.06
PERFORMANCE_FEE_RATE = 0.20
DEFAULT_UNIT_PRICE = 10000.0
EPSILON = 1e-6

# === PATHS ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"

DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

INVESTORS_FILE = DATA_DIR / "investors.csv"
TRANCHES_FILE = DATA_DIR / "tranches.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"

# === LEGACY UI CONFIG (retained for backward compatibility of imported constants) ===
PAGE_CONFIG = {
    "page_title": "He thong Quan Ly Quy",
    "page_icon": "$",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

CURRENCY_SYMBOL = " đ"

# === LEGACY SECURITY DEFAULT ===
# API runtime uses env vars `API_ADMIN_USERNAME` and `API_ADMIN_PASSWORD`.
ADMIN_PASSWORD = "1997"

# Legacy cache-related constants retained for compatibility.
CACHE_TTL_NAV = 120
CACHE_TTL_BALANCE = 60
CACHE_TTL_FEES = 300
DEBUG_MODE = False
