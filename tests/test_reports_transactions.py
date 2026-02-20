import csv
import importlib
from datetime import datetime
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
    db_file = Path(tempfile.gettempdir()) / f"backend_api_reports_{uuid.uuid4().hex}.db"
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


def _auth_header(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
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
    return response.json()["data"]["id"]


def _create_transaction(client: TestClient, headers: dict[str, str], payload: dict):
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 200


def _seed_holdings_without_period_transactions(client: TestClient, headers: dict[str, str]) -> tuple[int, int]:
    investor_1 = _create_investor(client, headers, f"Investor A {uuid.uuid4().hex[:6]}")
    investor_2 = _create_investor(client, headers, f"Investor B {uuid.uuid4().hex[:6]}")

    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "deposit",
            "investor_id": investor_1,
            "amount": 1_000_000,
            "total_nav": 1_000_000,
            "transaction_date": "2026-01-10",
        },
    )
    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "deposit",
            "investor_id": investor_2,
            "amount": 1_000_000,
            "total_nav": 2_000_000,
            "transaction_date": "2026-01-15",
        },
    )
    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "nav_update",
            "total_nav": 2_200_000,
            "transaction_date": "2026-02-20",
        },
    )

    return investor_1, investor_2


def _seed_mixed_transactions(client: TestClient, headers: dict[str, str]) -> int:
    investor_id = _create_investor(client, headers, f"Investor Mix {uuid.uuid4().hex[:6]}")

    _create_transaction(
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
    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "deposit",
            "investor_id": investor_id,
            "amount": 200_000,
            "total_nav": 1_200_000,
            "transaction_date": "2026-02-05",
        },
    )
    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "nav_update",
            "total_nav": 1_260_000,
            "transaction_date": "2026-02-20",
        },
    )

    return investor_id


def _seed_fee_drag_case(client: TestClient, headers: dict[str, str]) -> int:
    investor_id = _create_investor(client, headers, f"Investor Fee {uuid.uuid4().hex[:6]}")

    _create_transaction(
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
    _create_transaction(
        client,
        headers,
        {
            "transaction_type": "nav_update",
            "total_nav": 1_100_000,
            "transaction_date": "2026-02-10",
        },
    )

    runtime_module = importlib.import_module("backend_api.app.services.fund_runtime")
    models_module = importlib.import_module("core.models")
    runtime = runtime_module.runtime
    transaction_cls = models_module.Transaction

    def _write(manager):
        next_id = max((tx.id for tx in manager.transactions), default=0) + 1
        manager.transactions.append(
            transaction_cls(
                id=next_id,
                investor_id=investor_id,
                date=datetime(2026, 2, 15, 0, 0, 0),
                type="Phí",
                amount=-100_000,
                nav=1_000_000,
                units_change=-0.09090909,
            )
        )

    runtime.mutate(_write)
    return investor_id


def test_transactions_report_auto_swaps_date_and_keeps_investor_market_pl(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        investor_1, _ = _seed_holdings_without_period_transactions(client, headers)

        response = client.get(
            f"/api/v1/reports/transactions?investor_id={investor_1}&start_date=2026-02-01&end_date=2026-02-28",
            headers=headers,
        )
        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert summary["total_count"] == 0
        assert abs(summary["gross_profit_loss"] - 100_000) < 0.1
        assert abs(summary["gross_profit_loss_percent"] - 0.1) < 0.0001

        swapped_response = client.get(
            f"/api/v1/reports/transactions?investor_id={investor_1}&start_date=2026-02-28&end_date=2026-02-01",
            headers=headers,
        )
        assert swapped_response.status_code == 200
        swapped_summary = swapped_response.json()["data"]["summary"]
        assert abs(swapped_summary["gross_profit_loss"] - summary["gross_profit_loss"]) < 0.1
        assert abs(swapped_summary["gross_profit_loss_percent"] - summary["gross_profit_loss_percent"]) < 0.0001


def test_transactions_report_tx_type_only_changes_item_list(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        _seed_mixed_transactions(client, headers)

        base = client.get(
            "/api/v1/reports/transactions?start_date=2026-02-01&end_date=2026-02-28",
            headers=headers,
        )
        assert base.status_code == 200
        base_data = base.json()["data"]

        filtered = client.get(
            "/api/v1/reports/transactions?start_date=2026-02-01&end_date=2026-02-28&tx_type=deposit",
            headers=headers,
        )
        assert filtered.status_code == 200
        filtered_data = filtered.json()["data"]

        assert filtered_data["total"] < base_data["total"]
        assert filtered_data["summary"]["gross_profit_loss"] == base_data["summary"]["gross_profit_loss"]
        assert (
            filtered_data["summary"]["gross_profit_loss_percent"]
            == base_data["summary"]["gross_profit_loss_percent"]
        )
        assert filtered_data["summary"]["total_deposits"] == base_data["summary"]["total_deposits"]
        assert filtered_data["summary"]["total_withdrawals"] == base_data["summary"]["total_withdrawals"]


def test_transactions_report_excludes_fee_drag_from_market_pl(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        investor_id = _seed_fee_drag_case(client, headers)

        response = client.get(
            f"/api/v1/reports/transactions?investor_id={investor_id}&start_date=2026-02-01&end_date=2026-02-28",
            headers=headers,
        )
        assert response.status_code == 200
        summary = response.json()["data"]["summary"]

        assert summary["total_deposits"] == 0
        assert summary["total_withdrawals"] == 0
        assert abs(summary["gross_profit_loss"] - 100_000) < 2
        assert abs(summary["gross_profit_loss_percent"] - 0.1) < 0.001


def test_transactions_report_percent_uses_first_non_zero_base_for_full_range(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        investor_id = _create_investor(client, headers, f"Investor FullRange {uuid.uuid4().hex[:6]}")

        _create_transaction(
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
        _create_transaction(
            client,
            headers,
            {
                "transaction_type": "nav_update",
                "total_nav": 1_100_000,
                "transaction_date": "2026-06-01",
            },
        )

        response = client.get(
            f"/api/v1/reports/transactions?investor_id={investor_id}",
            headers=headers,
        )
        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert abs(summary["gross_profit_loss"] - 100_000) < 1
        assert abs(summary["gross_profit_loss_percent"] - 0.1) < 0.001


def test_transactions_export_includes_same_profit_percent_as_report(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        investor_id = _seed_mixed_transactions(client, headers)

        report = client.get(
            f"/api/v1/reports/transactions?investor_id={investor_id}&start_date=2026-02-01&end_date=2026-02-28",
            headers=headers,
        )
        assert report.status_code == 200
        expected_percent = report.json()["data"]["summary"]["gross_profit_loss_percent"]

        csv_response = client.get(
            f"/api/v1/reports/transactions/export?format=csv&investor_id={investor_id}"
            "&start_date=2026-02-01&end_date=2026-02-28&tx_type=deposit",
            headers=headers,
        )
        assert csv_response.status_code == 200
        assert csv_response.headers["content-type"].startswith("text/csv")
        assert "attachment" in csv_response.headers.get("content-disposition", "")
        assert csv_response.content.startswith(b"\xef\xbb\xbf")

        decoded = csv_response.content.decode("utf-8-sig")
        rows = list(csv.reader(StringIO(decoded)))
        percent_row = next(row for row in rows if row and row[0].startswith("%"))
        assert percent_row[1] == f"{expected_percent * 100:.2f}%"
        assert any(row and row[0] == "ID" for row in rows)

        pdf_response = client.get(
            f"/api/v1/reports/transactions/export?format=pdf&investor_id={investor_id}"
            "&start_date=2026-02-01&end_date=2026-02-28",
            headers=headers,
        )
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"].startswith("application/pdf")
        assert "attachment" in pdf_response.headers.get("content-disposition", "")
        assert pdf_response.content.startswith(b"%PDF")
