#!/usr/bin/env python3
r"""
Restore a local CNFund backup Excel file into PostgreSQL business tables.

Usage:
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --local-file "D:\\...\\CNFund_Backup_*.xlsx"
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --database-url "<postgres-url>" --local-file "D:\\...\\backup.xlsx"
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend_api.app.services.backup_service import restore_from_local_backup
from core.postgres_data_handler import PostgresDataHandler
from core.services_enhanced import EnhancedFundManager


EXPORT_DIR = Path("exports")


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

    env_file = Path(".env")
    for key in ("API_DATABASE_URL", "DATABASE_URL"):
        value = _read_env_file_value(env_file, key)
        if value:
            return value

    raise RuntimeError("Missing database URL. Set API_DATABASE_URL/DATABASE_URL or pass --database-url")


def _stage_local_backup(local_file: str) -> Path:
    source = Path(local_file)
    if not source.exists():
        raise FileNotFoundError(f"Local backup file not found: {source}")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = EXPORT_DIR / source.name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore local backup Excel into PostgreSQL business tables",
    )
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL")
    parser.add_argument("--local-file", required=True, help="Path to local .xlsx backup file")
    parser.add_argument(
        "--create-safety-backup",
        action="store_true",
        help="Create a manual safety backup before restore",
    )
    args = parser.parse_args()

    database_url = _resolve_database_url(args.database_url)
    local_path = _stage_local_backup(args.local_file)
    file_name = local_path.name

    print("Using database URL for migration (masked).")
    print(f"Using local backup file: {local_path}")

    handler = PostgresDataHandler(database_url=database_url)
    manager = EnhancedFundManager(handler, enable_snapshots=False)
    manager.load_data()
    manager._ensure_fund_manager_exists()

    result = restore_from_local_backup(
        manager,
        backup_id=file_name,
        create_safety_backup=args.create_safety_backup,
    )
    stats = handler.get_database_stats()

    print("Migration completed.")
    print(f"Restored sheets: {result.get('restored_sheets', [])}")
    print(f"Table counts: {stats.get('table_counts', {})}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise
