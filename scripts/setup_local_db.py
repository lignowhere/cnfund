#!/usr/bin/env python3
r"""
Set up a local PostgreSQL database from the latest .xlsx backup.

One-command recovery when Railway is unavailable:
  1. Checks local PostgreSQL connection
  2. Creates 'cnfund' database if needed
  3. Finds the latest backup in exports/ (or uses --file)
  4. Restores all fund data into local PostgreSQL

Usage:
  .\.venv\Scripts\python scripts\setup_local_db.py
  .\.venv\Scripts\python scripts\setup_local_db.py --file exports/Fund_Export_20260313_manual.xlsx
  .\.venv\Scripts\python scripts\setup_local_db.py --pg-user myuser --pg-password mypass --pg-port 5433
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPORT_DIR = REPO_ROOT / "exports"


def _find_latest_backup() -> Path | None:
    if not EXPORT_DIR.exists():
        return None
    backups = sorted(EXPORT_DIR.glob("Fund_Export_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return backups[0] if backups else None


def _check_pg_connection(host: str, port: int, user: str, password: str, dbname: str) -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
        conn.close()
        return True
    except Exception:
        return False


def _create_database(host: str, port: int, user: str, password: str, dbname: str) -> bool:
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone():
            print(f"  Database '{dbname}' already exists.")
            cur.close()
            conn.close()
            return True
        cur.execute(f'CREATE DATABASE "{dbname}"')  # noqa: S608
        print(f"  Created database '{dbname}'.")
        cur.close()
        conn.close()
        return True
    except Exception as exc:
        print(f"  Failed to create database: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up local PostgreSQL from latest backup")
    parser.add_argument("--file", default=None, help="Path to .xlsx backup file (default: latest in exports/)")
    parser.add_argument("--pg-host", default="localhost", help="PostgreSQL host (default: localhost)")
    parser.add_argument("--pg-port", type=int, default=5432, help="PostgreSQL port (default: 5432)")
    parser.add_argument("--pg-user", default="postgres", help="PostgreSQL user (default: postgres)")
    parser.add_argument("--pg-password", default="postgres", help="PostgreSQL password (default: postgres)")
    parser.add_argument("--pg-dbname", default="cnfund", help="Database name (default: cnfund)")
    args = parser.parse_args()

    # Step 1: Find backup file
    print("[1/4] Finding backup file...")
    if args.file:
        backup_path = Path(args.file)
        if not backup_path.exists():
            print(f"  ERROR: File not found: {backup_path}")
            return 1
    else:
        backup_path = _find_latest_backup()
        if not backup_path:
            print(f"  ERROR: No Fund_Export_*.xlsx files found in {EXPORT_DIR}")
            print("  Download a backup from Google Drive or copy one to exports/ first.")
            return 1
    print(f"  Using: {backup_path}")

    # Step 2: Check PostgreSQL and create database
    print("[2/4] Checking PostgreSQL connection...")
    if not _check_pg_connection(args.pg_host, args.pg_port, args.pg_user, args.pg_password, "postgres"):
        print(f"  ERROR: Cannot connect to PostgreSQL at {args.pg_host}:{args.pg_port}")
        print("  Make sure PostgreSQL is installed and running.")
        return 1
    print(f"  Connected to PostgreSQL at {args.pg_host}:{args.pg_port}")

    if not _create_database(args.pg_host, args.pg_port, args.pg_user, args.pg_password, args.pg_dbname):
        return 1

    # Step 3: Restore data
    database_url = f"postgresql://{args.pg_user}:{args.pg_password}@{args.pg_host}:{args.pg_port}/{args.pg_dbname}"

    print("[3/4] Restoring data from backup...")
    import shutil

    from backend_api.app.services.backup_service import restore_from_local_backup
    from core.postgres_data_handler import PostgresDataHandler
    from core.services_enhanced import EnhancedFundManager

    # Stage file to exports/ if not already there
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    staged = EXPORT_DIR / backup_path.name
    if backup_path.resolve() != staged.resolve():
        shutil.copy2(backup_path, staged)

    handler = PostgresDataHandler(database_url=database_url)
    manager = EnhancedFundManager(handler, enable_snapshots=False)
    manager.load_data()
    manager._ensure_fund_manager_exists()

    result = restore_from_local_backup(manager, backup_id=staged.name, create_safety_backup=False)

    sheets = result.get("restored_sheets", [])
    print(f"  Restored sheets: {sheets}")

    stats = handler.get_database_stats()
    counts = stats.get("table_counts", {})
    if counts:
        print(f"  Table counts: {counts}")

    # Step 4: Print ready-to-use config
    print("[4/4] Local database ready!")
    print()
    print("Add this to your .env file:")
    print(f"  API_DATABASE_URL={database_url}")
    print()
    print("Then run: npm run dev")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        raise
