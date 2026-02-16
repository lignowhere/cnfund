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
    db_file = Path(tempfile.gettempdir()) / f"backend_api_investor_contact_{uuid.uuid4().hex}.db"
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


def test_locations_endpoints(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        provinces_response = client.get("/api/v1/system/locations/provinces", headers=headers)
        assert provinces_response.status_code == 200
        provinces = provinces_response.json()["data"]
        assert len(provinces) > 0

        province_code = provinces[0]["code"]
        wards_response = client.get(
            f"/api/v1/system/locations/wards?province_code={province_code}",
            headers=headers,
        )
        assert wards_response.status_code == 200
        wards = wards_response.json()["data"]
        assert len(wards) > 0
        assert all(row["province_code"] == province_code for row in wards)


def test_investor_phone_validation_on_create_and_update(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        headers = _auth_header(client)
        provinces_response = client.get("/api/v1/system/locations/provinces", headers=headers)
        assert provinces_response.status_code == 200
        provinces = provinces_response.json()["data"]
        assert provinces
        province = provinces[0]

        wards_response = client.get(
            f"/api/v1/system/locations/wards?province_code={province['code']}",
            headers=headers,
        )
        assert wards_response.status_code == 200
        wards = wards_response.json()["data"]
        assert wards
        ward = wards[0]

        unique_suffix = uuid.uuid4().hex[:8]

        invalid_create = client.post(
            "/api/v1/investors",
            headers=headers,
            json={
                "name": "Phone Invalid Investor",
                "phone": "912345678.0",
                "email": f"invalid-phone-{unique_suffix}@example.com",
            },
        )
        assert invalid_create.status_code == 400

        valid_create = client.post(
            "/api/v1/investors",
            headers=headers,
            json={
                "name": "Phone Valid Investor",
                "phone": "0912345678",
                "email": f"valid-phone-{unique_suffix}@example.com",
                "join_date": "2026-02-16",
                "province_code": province["code"],
                "province_name": province["name"],
                "ward_code": ward["code"],
                "ward_name": ward["name"],
                "address_line": "123 Test Street",
            },
        )
        assert valid_create.status_code == 200
        investor_id = valid_create.json()["data"]["id"]

        invalid_update = client.put(
            f"/api/v1/investors/{investor_id}",
            headers=headers,
            json={"phone": "abc123"},
        )
        assert invalid_update.status_code == 400

        valid_update = client.put(
            f"/api/v1/investors/{investor_id}",
            headers=headers,
            json={
                "phone": "0900000000",
                "province_code": province["code"],
                "province_name": province["name"],
                "ward_code": ward["code"],
                "ward_name": ward["name"],
                "address_line": "45 New Address",
            },
        )
        assert valid_update.status_code == 200
        data = valid_update.json()["data"]
        assert data["phone"] == "0900000000"
        assert data["province_code"] == province["code"]
        assert data["ward_code"] == ward["code"]
