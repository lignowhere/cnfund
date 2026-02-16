import importlib

from fastapi.testclient import TestClient


def _load_app(monkeypatch):
    monkeypatch.setenv("API_DATABASE_URL", "sqlite:///./backend_api_smoke.db")
    monkeypatch.setenv("API_JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("API_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("API_ADMIN_PASSWORD", "admin123")

    main_module = importlib.import_module("backend_api.app.main")
    return main_module.app


def test_app_imports_without_streamlit(monkeypatch):
    app = _load_app(monkeypatch)
    assert app is not None


def test_health_endpoint(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200


def test_transactions_endpoint_requires_auth(monkeypatch):
    app = _load_app(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/api/v1/transactions")
        assert response.status_code in {401, 403}
