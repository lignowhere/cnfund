import csv
import importlib
from io import StringIO
from pathlib import Path
import sys
import tempfile
import uuid

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_app(monkeypatch):
    db_file = Path(tempfile.gettempdir()) / f"backend_api_accounts_{uuid.uuid4().hex}.db"
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
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


def _auth_header(client: TestClient, username: str, password: str) -> dict[str, str]:
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


def _create_transaction(client: TestClient, headers: dict[str, str], payload: dict):
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 200


def test_create_investor_account_conflicts(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client, "admin", "admin123")
        investor_1 = _create_investor(client, admin_headers, f"Investor A {uuid.uuid4().hex[:6]}")
        investor_2 = _create_investor(client, admin_headers, f"Investor B {uuid.uuid4().hex[:6]}")

        create_response = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_1,
                "username": "inv_a",
                "password": "secret123",
            },
        )
        assert create_response.status_code == 200
        assert create_response.json()["data"]["has_account"] is True

        duplicate_investor_response = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_1,
                "username": "inv_a_2",
                "password": "secret123",
            },
        )
        assert duplicate_investor_response.status_code == 409

        duplicate_username_response = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_2,
                "username": "inv_a",
                "password": "secret123",
            },
        )
        assert duplicate_username_response.status_code == 409


def test_investor_account_accepts_text_only_and_number_only_passwords(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client, "admin", "admin123")
        investor_id = _create_investor(client, admin_headers, f"Investor Pwd {uuid.uuid4().hex[:6]}")

        create_response = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_id,
                "username": "pwd_user",
                "password": "onlytext",
            },
        )
        assert create_response.status_code == 200

        text_only_login = _login(client, "pwd_user", "onlytext")
        assert text_only_login.status_code == 200

        reset_response = client.post(
            f"/api/v1/accounts/investors/{investor_id}/reset-password",
            headers=admin_headers,
            json={"new_password": "1234"},
        )
        assert reset_response.status_code == 200

        old_password_login = _login(client, "pwd_user", "onlytext")
        assert old_password_login.status_code == 401

        number_only_login = _login(client, "pwd_user", "1234")
        assert number_only_login.status_code == 200


def test_investor_self_endpoints_and_permissions(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client, "admin", "admin123")
        investor_a_name = f"Investor Self A {uuid.uuid4().hex[:6]}"
        investor_b_name = f"Investor Self B {uuid.uuid4().hex[:6]}"
        investor_a = _create_investor(client, admin_headers, investor_a_name)
        investor_b = _create_investor(client, admin_headers, investor_b_name)

        _create_transaction(
            client,
            admin_headers,
            {
                "transaction_type": "deposit",
                "investor_id": investor_a,
                "amount": 1_000_000,
                "total_nav": 1_000_000,
                "transaction_date": "2026-01-10",
            },
        )
        _create_transaction(
            client,
            admin_headers,
            {
                "transaction_type": "deposit",
                "investor_id": investor_b,
                "amount": 500_000,
                "total_nav": 1_500_000,
                "transaction_date": "2026-01-11",
            },
        )
        _create_transaction(
            client,
            admin_headers,
            {
                "transaction_type": "nav_update",
                "total_nav": 1_700_000,
                "transaction_date": "2026-01-12",
            },
        )

        create_account = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_a,
                "username": "self_user",
                "password": "secret123",
            },
        )
        assert create_account.status_code == 200

        investor_login = _login(client, "self_user", "secret123")
        assert investor_login.status_code == 200
        investor_access = investor_login.json()["data"]["access_token"]
        investor_headers = {"Authorization": f"Bearer {investor_access}"}

        me_response = client.get("/api/v1/auth/me", headers=investor_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()["data"]
        assert me_data["role"] == "investor"
        assert me_data["investor_id"] == investor_a

        my_report = client.get("/api/v1/reports/me", headers=investor_headers)
        assert my_report.status_code == 200
        assert my_report.json()["data"]["investor"]["id"] == investor_a

        my_transactions = client.get("/api/v1/reports/me/transactions", headers=investor_headers)
        assert my_transactions.status_code == 200
        rows = my_transactions.json()["data"]["items"]
        assert rows
        assert {row["investor_id"] for row in rows} == {investor_a}

        forbidden_investors = client.get("/api/v1/investors/cards", headers=investor_headers)
        assert forbidden_investors.status_code == 403

        forbidden_transactions = client.get("/api/v1/transactions", headers=investor_headers)
        assert forbidden_transactions.status_code == 403

        forbidden_report = client.get(f"/api/v1/reports/investor/{investor_b}", headers=investor_headers)
        assert forbidden_report.status_code == 403

        export_response = client.get(
            "/api/v1/reports/me/transactions/export?format=csv",
            headers=investor_headers,
        )
        assert export_response.status_code == 200
        assert "attachment" in export_response.headers.get("content-disposition", "")

        csv_text = export_response.text
        parsed = list(csv.reader(StringIO(csv_text)))
        data_rows = [row for row in parsed if len(row) >= 7 and row[0].isdigit()]
        assert data_rows
        assert all(row[1] == investor_a_name for row in data_rows)


def test_reset_password_and_disable_investor_account(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        admin_headers = _auth_header(client, "admin", "admin123")
        investor_id = _create_investor(client, admin_headers, f"Investor Lock {uuid.uuid4().hex[:6]}")

        create_account = client.post(
            "/api/v1/accounts/investors",
            headers=admin_headers,
            json={
                "investor_id": investor_id,
                "username": "lock_user",
                "password": "secret123",
            },
        )
        assert create_account.status_code == 200

        first_login = _login(client, "lock_user", "secret123")
        assert first_login.status_code == 200

        reset_response = client.post(
            f"/api/v1/accounts/investors/{investor_id}/reset-password",
            headers=admin_headers,
            json={"new_password": "newsecret123"},
        )
        assert reset_response.status_code == 200

        old_password_login = _login(client, "lock_user", "secret123")
        assert old_password_login.status_code == 401

        new_password_login = _login(client, "lock_user", "newsecret123")
        assert new_password_login.status_code == 200

        disable_response = client.patch(
            f"/api/v1/accounts/investors/{investor_id}",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert disable_response.status_code == 200
        assert disable_response.json()["data"]["is_active"] is False

        disabled_login = _login(client, "lock_user", "newsecret123")
        assert disabled_login.status_code == 403
