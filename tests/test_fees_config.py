import importlib
from pathlib import Path
import sys
import tempfile
import uuid

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_app(monkeypatch):
    db_file = Path(tempfile.gettempdir()) / f"backend_api_fees_config_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("API_DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("API_JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("API_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("API_ADMIN_PASSWORD", "admin123")

    for module_name in list(sys.modules):
        if module_name.startswith("backend_api.app"):
            del sys.modules[module_name]

    config_module = importlib.import_module("backend_api.app.core.config")
    config_module.get_settings.cache_clear()

    main_module = importlib.import_module("backend_api.app.main")
    return main_module.app


def _login(client: TestClient, username: str, password: str):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def _auth_header(client: TestClient, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = _login(client, username, password)
    assert response.status_code == 200
    access_token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _create_investor(client: TestClient, headers: dict[str, str], name: str) -> int:
    response = client.post(
        "/api/v1/investors",
        headers=headers,
        json={
            "name": name,
            "phone": "0912345678",
            "email": f"{uuid.uuid4().hex[:10]}@example.com",
            "join_date": "2026-01-01",
        },
    )
    assert response.status_code == 200
    return int(response.json()["data"]["id"])


def _create_tx(client: TestClient, headers: dict[str, str], payload: dict):
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 200


def _seed_investor_with_profit_case(client: TestClient, headers: dict[str, str], name_prefix: str) -> int:
    investor_id = _create_investor(client, headers, f"{name_prefix} {uuid.uuid4().hex[:6]}")
    _create_tx(
        client,
        headers,
        {
            "transaction_type": "deposit",
            "investor_id": investor_id,
            "amount": 1_000_000,
            "total_nav": 1_000_000,
            "transaction_date": "2026-01-10",
        },
    )
    _create_tx(
        client,
        headers,
        {
            "transaction_type": "nav_update",
            "total_nav": 1_200_000,
            "transaction_date": "2026-02-10",
        },
    )
    return investor_id


def test_fee_config_global_and_override_preview_flow(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client)
        investor_a = _seed_investor_with_profit_case(client, admin_headers, "Investor A")
        investor_b = _seed_investor_with_profit_case(client, admin_headers, "Investor B")

        initial_preview = client.post(
            "/api/v1/fees/preview",
            headers=admin_headers,
            json={"end_date": "2026-02-10", "total_nav": 1_200_000},
        )
        assert initial_preview.status_code == 200
        rows = initial_preview.json()["data"]["items"]
        assert rows
        assert all(abs(row["applied_performance_fee_rate"] - 0.2) < 1e-9 for row in rows)
        assert all(abs(row["applied_hurdle_rate"] - 0.06) < 1e-9 for row in rows)
        assert all(row["fee_source"] == "global" for row in rows)

        update_global = client.patch(
            "/api/v1/fees/config/global",
            headers=admin_headers,
            json={"performance_fee_rate": 0.15, "hurdle_rate_annual": 0.05},
        )
        assert update_global.status_code == 200
        updated_global = update_global.json()["data"]
        assert abs(updated_global["performance_fee_rate"] - 0.15) < 1e-9
        assert abs(updated_global["hurdle_rate_annual"] - 0.05) < 1e-9

        override_a = client.put(
            f"/api/v1/fees/config/overrides/{investor_a}",
            headers=admin_headers,
            json={"performance_fee_rate": 0.1, "hurdle_rate_annual": 0.02},
        )
        assert override_a.status_code == 200

        with_override_preview = client.post(
            "/api/v1/fees/preview",
            headers=admin_headers,
            json={"end_date": "2026-02-10", "total_nav": 1_200_000},
        )
        assert with_override_preview.status_code == 200
        rows_by_id = {row["investor_id"]: row for row in with_override_preview.json()["data"]["items"]}

        assert rows_by_id[investor_a]["fee_source"] == "override"
        assert abs(rows_by_id[investor_a]["applied_performance_fee_rate"] - 0.1) < 1e-9
        assert abs(rows_by_id[investor_a]["applied_hurdle_rate"] - 0.02) < 1e-9

        assert rows_by_id[investor_b]["fee_source"] == "global"
        assert abs(rows_by_id[investor_b]["applied_performance_fee_rate"] - 0.15) < 1e-9
        assert abs(rows_by_id[investor_b]["applied_hurdle_rate"] - 0.05) < 1e-9

        delete_override = client.delete(
            f"/api/v1/fees/config/overrides/{investor_a}",
            headers=admin_headers,
        )
        assert delete_override.status_code == 200

        after_delete_preview = client.post(
            "/api/v1/fees/preview",
            headers=admin_headers,
            json={"end_date": "2026-02-10", "total_nav": 1_200_000},
        )
        assert after_delete_preview.status_code == 200
        rows_after_delete = {row["investor_id"]: row for row in after_delete_preview.json()["data"]["items"]}
        assert rows_after_delete[investor_a]["fee_source"] == "global"
        assert abs(rows_after_delete[investor_a]["applied_performance_fee_rate"] - 0.15) < 1e-9


def test_fee_config_applies_to_withdrawal(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client)
        investor_id = _seed_investor_with_profit_case(client, admin_headers, "Investor Withdrawal")

        override = client.put(
            f"/api/v1/fees/config/overrides/{investor_id}",
            headers=admin_headers,
            json={"performance_fee_rate": 0.0},
        )
        assert override.status_code == 200

        _create_tx(
            client,
            admin_headers,
            {
                "transaction_type": "withdraw",
                "investor_id": investor_id,
                "amount": 100_000,
                "total_nav": 1_100_000,
                "transaction_date": "2026-02-11",
            },
        )

        runtime_module = importlib.import_module("backend_api.app.services.fund_runtime")
        runtime = runtime_module.runtime

        def _read(manager):
            return [
                tx
                for tx in manager.transactions
                if tx.investor_id == investor_id and str(tx.type).strip().lower().startswith("ph")
            ]

        fee_transactions = runtime.read(_read)
        assert fee_transactions == []


def test_fee_preview_token_mismatch_when_config_changes(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client)
        _seed_investor_with_profit_case(client, admin_headers, "Investor Token")

        preview_response = client.post(
            "/api/v1/fees/preview",
            headers=admin_headers,
            json={"end_date": "2026-02-10", "total_nav": 1_200_000},
        )
        assert preview_response.status_code == 200
        confirm_token = preview_response.json()["data"]["confirm_token"]

        update_global = client.patch(
            "/api/v1/fees/config/global",
            headers=admin_headers,
            json={"performance_fee_rate": 0.1},
        )
        assert update_global.status_code == 200

        apply_response = client.post(
            "/api/v1/fees/apply",
            headers=admin_headers,
            json={
                "year": 2026,
                "end_date": "2026-02-10",
                "total_nav": 1_200_000,
                "confirm_token": confirm_token,
                "acknowledge_risk": True,
                "acknowledge_backup": True,
            },
        )
        assert apply_response.status_code == 409


def test_fee_config_permissions_for_viewer(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client)
        investor_id = _create_investor(client, admin_headers, f"Investor Perm {uuid.uuid4().hex[:6]}")

        database_module = importlib.import_module("backend_api.app.core.database")
        models_module = importlib.import_module("backend_api.app.models.auth")
        security_module = importlib.import_module("backend_api.app.core.security")

        db = database_module.SessionLocal()
        try:
            db.add(
                models_module.User(
                    username="viewer_fee",
                    password_hash=security_module.get_password_hash("viewer123"),
                    role="viewer",
                    is_active=True,
                )
            )
            db.commit()
        finally:
            db.close()

        viewer_headers = _auth_header(client, "viewer_fee", "viewer123")

        read_config = client.get("/api/v1/fees/config", headers=viewer_headers)
        assert read_config.status_code == 200

        patch_forbidden = client.patch(
            "/api/v1/fees/config/global",
            headers=viewer_headers,
            json={"performance_fee_rate": 0.11},
        )
        assert patch_forbidden.status_code == 403

        put_forbidden = client.put(
            f"/api/v1/fees/config/overrides/{investor_id}",
            headers=viewer_headers,
            json={"performance_fee_rate": 0.11},
        )
        assert put_forbidden.status_code == 403

        delete_forbidden = client.delete(
            f"/api/v1/fees/config/overrides/{investor_id}",
            headers=viewer_headers,
        )
        assert delete_forbidden.status_code == 403


def test_backup_restore_persists_fee_config(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client)
        investor_id = _create_investor(client, admin_headers, f"Investor Backup {uuid.uuid4().hex[:6]}")

        set_global = client.patch(
            "/api/v1/fees/config/global",
            headers=admin_headers,
            json={"performance_fee_rate": 0.17, "hurdle_rate_annual": 0.07},
        )
        assert set_global.status_code == 200
        set_override = client.put(
            f"/api/v1/fees/config/overrides/{investor_id}",
            headers=admin_headers,
            json={"performance_fee_rate": 0.09},
        )
        assert set_override.status_code == 200

        backup_response = client.post("/api/v1/backups/manual", headers=admin_headers)
        assert backup_response.status_code == 200
        backup_id = backup_response.json()["data"]["backup_id"]

        mutate_global = client.patch(
            "/api/v1/fees/config/global",
            headers=admin_headers,
            json={"performance_fee_rate": 0.2, "hurdle_rate_annual": 0.06},
        )
        assert mutate_global.status_code == 200
        mutate_override = client.delete(
            f"/api/v1/fees/config/overrides/{investor_id}",
            headers=admin_headers,
        )
        assert mutate_override.status_code == 200

        restore_response = client.post(
            "/api/v1/backups/restore",
            headers=admin_headers,
            json={
                "backup_id": backup_id,
                "confirm_phrase": "RESTORE",
                "create_safety_backup": False,
            },
        )
        assert restore_response.status_code == 200

        config_after_restore = client.get("/api/v1/fees/config", headers=admin_headers)
        assert config_after_restore.status_code == 200
        payload = config_after_restore.json()["data"]
        assert abs(payload["global_config"]["performance_fee_rate"] - 0.17) < 1e-9
        assert abs(payload["global_config"]["hurdle_rate_annual"] - 0.07) < 1e-9
        overrides = {row["investor_id"]: row for row in payload["overrides"]}
        assert investor_id in overrides
        assert abs(overrides[investor_id]["performance_fee_rate"] - 0.09) < 1e-9
