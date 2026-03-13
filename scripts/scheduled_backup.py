#!/usr/bin/env python3
r"""
Periodic backup — run via cron, Windows Task Scheduler, or manually.

Creates a .xlsx backup of the current database and optionally uploads to Google Drive.

Usage:
  .\.venv\Scripts\python scripts\scheduled_backup.py
  .\.venv\Scripts\python scripts\scheduled_backup.py --database-url "postgresql://..."
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def _read_env_file_value(file_path: Path, key: str) -> str | None:
    if not file_path.exists():
        return None
    for raw in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        left, right = line.split("=", 1)
        if left.strip() == key:
            return _strip_quotes(right.strip())
    return None


def _resolve_database_url(cli_value: str | None) -> str:
    if cli_value:
        return cli_value

    for key in ("API_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return _strip_quotes(value)

    for env_file in (REPO_ROOT / ".env", REPO_ROOT / "backend_api" / ".env"):
        for key in ("API_DATABASE_URL", "DATABASE_URL"):
            value = _read_env_file_value(env_file, key)
            if value:
                return value

    raise RuntimeError(
        "Missing database URL. Set API_DATABASE_URL/DATABASE_URL or pass --database-url"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a scheduled backup of the CNFund database",
    )
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print config and exit without creating backup",
    )
    args = parser.parse_args()

    database_url = _resolve_database_url(args.database_url)
    print(f"Database: {'*' * 20} (masked)")

    if args.dry_run:
        print("Dry run — no backup created.")
        return 0

    from backend_api.app.services.backup_service import trigger_manual_backup
    from core.postgres_data_handler import PostgresDataHandler
    from core.services_enhanced import EnhancedFundManager

    handler = PostgresDataHandler(database_url=database_url)
    manager = EnhancedFundManager(handler, enable_snapshots=False)
    manager.load_data()

    result = trigger_manual_backup(manager, description="scheduled")

    backup_id = result.get("backup_id", "unknown")
    drive_ok = result.get("google_drive_uploaded", False)
    drive_link = result.get("google_drive_link") or ""
    drive_reason = result.get("google_drive_reason") or "not configured"

    print(f"Backup created: {backup_id}")
    print(f"  Local:  exports/{backup_id}")
    print(f"  Drive:  {'OK ' + drive_link if drive_ok else 'SKIP — ' + drive_reason}")

    stats = handler.get_database_stats()
    counts = stats.get("table_counts", {})
    if counts:
        print(f"  Tables: {counts}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        raise
