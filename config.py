from pathlib import Path
from datetime import datetime

# === FUND CONSTANTS ===
HURDLE_RATE_ANNUAL = 0.06
PERFORMANCE_FEE_RATE = 0.20
DEFAULT_UNIT_PRICE = 1000.0
EPSILON = 1e-6

# === PATHS ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"

# Tạo thư mục
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# Files
INVESTORS_FILE = DATA_DIR / "investors.csv"
TRANCHES_FILE = DATA_DIR / "tranches.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"

# === UI CONFIG ===
PAGE_CONFIG = {
    "page_title": "Fund Management System",
    "page_icon": "💰",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

CURRENCY_SYMBOL = "đ"
# === SECURITY ===
ADMIN_PASSWORD = "1997"  # Placeholder tạm; sẽ override ở app.py bằng secrets/env var. Thay tạm nếu cần test.
