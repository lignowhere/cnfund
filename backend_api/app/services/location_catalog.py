from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


class WardRecord(TypedDict):
    code: str
    name: str
    province_code: str


class ProvinceRecord(TypedDict):
    code: str
    name: str
    wards: list[WardRecord]


def _snapshot_path() -> Path:
    # backend_api/app/services -> backend_api/app
    app_root = Path(__file__).resolve().parents[1]
    return app_root / "data" / "locations" / "vn_only_simplified_json_generated_data_vn_units.json"


@lru_cache
def load_location_catalog() -> list[ProvinceRecord]:
    path = _snapshot_path()
    if not path.exists():
        raise RuntimeError(f"Missing location snapshot: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    provinces: list[ProvinceRecord] = []
    for item in raw:
        province_code = str(item.get("Code", "")).strip()
        province_name = str(item.get("FullName", "")).strip()
        if not province_code or not province_name:
            continue

        wards: list[WardRecord] = []
        for ward in item.get("Wards", []) or []:
            ward_code = str(ward.get("Code", "")).strip()
            ward_name = str(ward.get("FullName", "")).strip()
            ward_province_code = str(ward.get("ProvinceCode", province_code)).strip() or province_code
            if not ward_code or not ward_name:
                continue
            wards.append(
                {
                    "code": ward_code,
                    "name": ward_name,
                    "province_code": ward_province_code,
                }
            )

        wards.sort(key=lambda row: row["name"])
        provinces.append(
            {
                "code": province_code,
                "name": province_name,
                "wards": wards,
            }
        )

    provinces.sort(key=lambda row: row["name"])
    return provinces


def get_provinces() -> list[dict[str, str]]:
    return [{"code": row["code"], "name": row["name"]} for row in load_location_catalog()]


def get_wards(province_code: str) -> list[dict[str, str]]:
    wanted = province_code.strip()
    if not wanted:
        return []
    for province in load_location_catalog():
        if province["code"] == wanted:
            return [
                {
                    "code": ward["code"],
                    "name": ward["name"],
                    "province_code": ward["province_code"],
                }
                for ward in province["wards"]
            ]
    return []
