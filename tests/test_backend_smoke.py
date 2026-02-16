import importlib
from pathlib import Path
import sys
import tempfile
import uuid

from fastapi.testclient import TestClient


def _load_app(monkeypatch):
    db_file = Path(tempfile.gettempdir()) / f"backend_api_smoke_{uuid.uuid4().hex}.db"
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
