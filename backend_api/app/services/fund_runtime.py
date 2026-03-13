import sys
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Callable, TypeVar

from ..core.config import get_settings


T = TypeVar("T")


class FundRuntime:
    """Thread-safe runtime around existing CNFund business logic."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._settings = get_settings()
        self._bootstrap_sys_path()
        self._manager = self._build_manager()
        self._dirty = False

    def _bootstrap_sys_path(self) -> None:
        # backend_api/app/services -> backend_api/app -> backend_api -> repo root
        repo_root = Path(__file__).resolve().parents[3]
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)

    def _build_manager(self):
        database_url = (self._settings.database_url or "").strip()
        if not database_url:
            raise RuntimeError(
                "Missing API_DATABASE_URL. Runtime is PostgreSQL-only and requires a database URL."
            )

        from core.postgres_data_handler import PostgresDataHandler  # type: ignore

        handler = PostgresDataHandler(database_url=database_url)

        from core.services_enhanced import EnhancedFundManager  # type: ignore

        manager = EnhancedFundManager(handler)
        manager.load_data()
        manager._ensure_fund_manager_exists()
        return manager

    def refresh(self) -> None:
        self._manager.load_data()
        self._manager._ensure_fund_manager_exists()

    def read(self, callback: Callable[[object], T]) -> T:
        with self._lock:
            if self._dirty:
                self.refresh()
                self._dirty = False
            return callback(self._manager)

    def mutate(self, callback: Callable[[object], T]) -> T:
        with self._lock:
            self.refresh()
            result = callback(self._manager)
            self._manager.save_data()
            self._dirty = True
            return result

    @staticmethod
    def as_datetime(tx_date: date | datetime) -> datetime:
        if isinstance(tx_date, datetime):
            return tx_date
        return datetime.combine(tx_date, datetime.min.time())


_runtime: FundRuntime | None = None
_runtime_lock = threading.Lock()


def get_runtime() -> FundRuntime:
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                _runtime = FundRuntime()
    return _runtime


# Backward-compatible module-level access
def __getattr__(name: str):
    if name == "runtime":
        return get_runtime()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
