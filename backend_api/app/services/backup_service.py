from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


EXPORT_DIR = Path("exports")
DATA_DIR = Path("data")
SHEET_TO_FILE = {
    "Investors": "investors.csv",
    "Tranches": "tranches.csv",
    "Transactions": "transactions.csv",
    "Fee_Records": "fee_records.csv",
}


def list_local_backups(days: int = 30) -> list[dict[str, Any]]:
    EXPORT_DIR.mkdir(exist_ok=True)
    cutoff = datetime.now() - timedelta(days=days)
    items: list[dict[str, Any]] = []
    for path in EXPORT_DIR.glob("Fund_Export_*.xlsx"):
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        if modified < cutoff:
            continue
        filename = path.name
        if "auto_" in filename:
            backup_type = "auto"
        elif "manual" in filename:
            backup_type = "manual"
        else:
            backup_type = "unknown"
        items.append(
            {
                "backup_id": filename,
                "backup_type": backup_type,
                "created_at": modified.isoformat(),
                "size_kb": round(stat.st_size / 1024, 1),
                "path": str(path),
            }
        )
    items.sort(key=lambda row: row["created_at"], reverse=True)
    return items


def trigger_manual_backup(fund_manager, description: str = "api_manual") -> dict[str, Any]:
    try:
        from integrations.auto_backup_personal import manual_backup

        success = manual_backup(fund_manager, description)
        if not success:
            raise RuntimeError("manual backup failed")
    except Exception as exc:
        raise RuntimeError(f"manual backup failed: {exc}") from exc

    backups = list_local_backups(days=365)
    if not backups:
        raise RuntimeError("backup completed but no local backup file found")
    return backups[0]


def restore_from_local_backup(
    fund_manager,
    backup_id: str,
    *,
    create_safety_backup: bool = True,
) -> dict[str, Any]:
    target = EXPORT_DIR / backup_id
    if not target.exists():
        raise FileNotFoundError(f"backup file not found: {backup_id}")

    if create_safety_backup:
        try:
            trigger_manual_backup(fund_manager, description="pre_restore_safety")
        except Exception:
            # Non-blocking: restore can still continue.
            pass

    excel_data = pd.read_excel(target, sheet_name=None)
    DATA_DIR.mkdir(exist_ok=True)

    restored_sheets: list[str] = []
    for sheet_name, csv_name in SHEET_TO_FILE.items():
        if sheet_name not in excel_data:
            continue
        output_path = DATA_DIR / csv_name
        excel_data[sheet_name].to_csv(output_path, index=False)
        restored_sheets.append(sheet_name)

    fund_manager.load_data()
    fund_manager._ensure_fund_manager_exists()

    return {
        "restored": True,
        "backup_id": backup_id,
        "restored_sheets": restored_sheets,
    }

