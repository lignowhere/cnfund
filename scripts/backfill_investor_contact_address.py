#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.postgres_data_handler import PostgresDataHandler
from core.services_enhanced import EnhancedFundManager


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


def normalize_phone(phone: str) -> tuple[str, str]:
    raw = str(phone or "").strip()
    if not raw:
        return "", "empty"

    if raw.endswith(".0") and raw[:-2].replace(".", "", 1).isdigit():
        raw = raw[:-2]

    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return "", "invalid_non_digit"
    if len(digits) == 9:
        digits = f"0{digits}"
    if re.fullmatch(r"0\d{9}", digits):
        return digits, "normalized"
    return "", "invalid_length_or_prefix"


def write_report(rows: list[dict[str, str]]) -> Path:
    output_dir = Path("exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"investor_contact_backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "investor_id",
                "investor_name",
                "old_phone",
                "new_phone",
                "phone_status",
                "address_line_seeded",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill investor phone/address fields for PostgreSQL runtime data",
    )
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, do not persist changes")
    args = parser.parse_args()

    database_url = _resolve_database_url(args.database_url)
    handler = PostgresDataHandler(database_url=database_url)
    manager = EnhancedFundManager(handler, enable_snapshots=False)
    manager.load_data()
    manager._ensure_fund_manager_exists()

    updated_count = 0
    invalid_count = 0
    seeded_address_line_count = 0
    report_rows: list[dict[str, str]] = []

    for investor in manager.get_regular_investors():
        old_phone = str(getattr(investor, "phone", "") or "").strip()
        new_phone, phone_status = normalize_phone(old_phone)
        phone_changed = old_phone != new_phone
        address_line_seeded = False

        if phone_status.startswith("invalid"):
            invalid_count += 1

        if phone_changed:
            investor.phone = new_phone
            updated_count += 1

        province_code = str(getattr(investor, "province_code", "") or "").strip()
        ward_code = str(getattr(investor, "ward_code", "") or "").strip()
        has_structured_address = bool(province_code and ward_code)
        address_value = str(getattr(investor, "address", "") or "").strip()
        address_line_value = str(getattr(investor, "address_line", "") or "").strip()

        if not has_structured_address and address_value and not address_line_value:
            investor.address_line = address_value
            address_line_seeded = True
            seeded_address_line_count += 1
            updated_count += 1

        report_rows.append(
            {
                "investor_id": str(investor.id),
                "investor_name": investor.name,
                "old_phone": old_phone,
                "new_phone": new_phone,
                "phone_status": phone_status,
                "address_line_seeded": "yes" if address_line_seeded else "no",
                "note": "manual_review_required" if phone_status.startswith("invalid") else "",
            }
        )

    if not args.dry_run:
        if not manager.save_data():
            raise RuntimeError("Failed to persist backfill changes")

    report_path = write_report(report_rows)
    print("Backfill completed.")
    print(f"Dry-run: {args.dry_run}")
    print(f"Investors scanned: {len(report_rows)}")
    print(f"Records updated: {updated_count}")
    print(f"Invalid phones cleared: {invalid_count}")
    print(f"Address line seeded from legacy address: {seeded_address_line_count}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
