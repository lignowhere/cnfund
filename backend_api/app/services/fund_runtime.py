import os
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

    def _bootstrap_sys_path(self) -> None:
        # backend_api/app/services -> backend_api/app -> backend_api -> repo root
        repo_root = Path(__file__).resolve().parents[3]
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)

    def _build_manager(self):
        source = (self._settings.cnfund_data_source or os.getenv("CNFUND_DATA_SOURCE", "csv")).lower()
        if source == "drive":
            from core.drive_data_handler import DriveBackedDataManager  # type: ignore

            handler = DriveBackedDataManager()
        else:
            from core.csv_data_handler import CSVDataHandler  # type: ignore

            handler = CSVDataHandler()

        from core.services_enhanced import EnhancedFundManager  # type: ignore

        manager = EnhancedFundManager(handler)
        manager.load_data()
        manager._ensure_fund_manager_exists()
        return manager

    def refresh(self) -> None:
        self._manager.load_data()
        self._manager._ensure_fund_manager_exists()

    def read(self, callback: Callable[[object], T]) -> T:
        self.refresh()
        return callback(self._manager)

    def mutate(self, callback: Callable[[object], T]) -> T:
        with self._lock:
            self.refresh()
            result = callback(self._manager)
            self._manager.save_data()
            self.refresh()
            return result

    @staticmethod
    def as_datetime(tx_date: date | datetime) -> datetime:
        if isinstance(tx_date, datetime):
            return tx_date
        return datetime.combine(tx_date, datetime.now().time())


runtime = FundRuntime()

