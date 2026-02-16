#!/usr/bin/env python3
r"""
Download latest CNFund backup file from Google Drive and restore into PostgreSQL.

Usage:
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --database-url "<postgres-url>"
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --name-filter Fund_Export
  .\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --local-file "D:\...\CNFund_Backup_*.xlsx"
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from googleapiclient.http import MediaIoBaseDownload

from backend_api.app.services.backup_service import restore_from_local_backup
from core.postgres_data_handler import PostgresDataHandler
from core.services_enhanced import EnhancedFundManager
from integrations.google_drive_oauth import GoogleDriveOAuthManager


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


def _normalize_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def _find_latest_drive_backup(
    drive_manager: GoogleDriveOAuthManager,
    name_filter: str | None = None,
) -> dict[str, Any]:
    if not drive_manager.service:
        raise RuntimeError("Google Drive service is not initialized")
    if not drive_manager.folder_id:
        raise RuntimeError("Google Drive folder_id is empty")

    query = (
        f"'{drive_manager.folder_id}' in parents and "
        "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and "
        "trashed=false"
    )

    results = drive_manager.service.files().list(
        q=query,
        orderBy="modifiedTime desc",
        pageSize=50,
        fields="files(id,name,modifiedTime,size,webViewLink)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    files = results.get("files", [])
    if not files:
        raise RuntimeError("No .xlsx files found in Google Drive folder")

    preferred_patterns = ["fund_export", "cnfund_backup"]
    selected = None

    for file_info in files:
        file_name = _normalize_name(file_info.get("name"))
        if name_filter and _normalize_name(name_filter) not in file_name:
            continue
        if any(pattern in file_name for pattern in preferred_patterns):
            selected = file_info
            break

    if selected is None and name_filter:
        raise RuntimeError(f"No Drive file matched name filter: {name_filter}")
    if selected is None:
        selected = files[0]

    return selected


def _download_drive_file(drive_manager: GoogleDriveOAuthManager, file_id: str, output_path: Path) -> None:
    if not drive_manager.service:
        raise RuntimeError("Google Drive service is not initialized")

    request = drive_manager.service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(buffer.read())


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
        description="Migrate latest Google Drive backup into PostgreSQL business tables",
    )
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL")
    parser.add_argument(
        "--name-filter",
        default=None,
        help="Optional name filter to pick a specific backup pattern (e.g. Fund_Export)",
    )
    parser.add_argument(
        "--create-safety-backup",
        action="store_true",
        help="Create a manual safety backup before restore",
    )
    parser.add_argument(
        "--local-file",
        default=None,
        help="Use a local .xlsx backup file instead of downloading from Google Drive",
    )
    args = parser.parse_args()

    database_url = _resolve_database_url(args.database_url)
    print("Using database URL for migration (masked).")

    if args.local_file:
        local_path = _stage_local_backup(args.local_file)
        file_name = local_path.name
        print(f"Using local backup file: {local_path}")
    else:
        drive = GoogleDriveOAuthManager()
        if not drive.connected:
            raise RuntimeError("Google Drive OAuth is not connected. Check token.pickle/oauth setup.")

        latest = _find_latest_drive_backup(drive, name_filter=args.name_filter)
        file_name = str(latest.get("name") or "latest_drive_backup.xlsx")
        file_id = str(latest.get("id") or "")
        if not file_id:
            raise RuntimeError("Drive file id is missing")

        local_path = EXPORT_DIR / file_name
        print(f"Downloading latest backup: {file_name}")
        _download_drive_file(drive, file_id, local_path)
        print(f"Downloaded to: {local_path}")

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
