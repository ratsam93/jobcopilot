from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend.app.auth import auth_service
from apps.backend.app.main import app


client = TestClient(app)


def test_login_returns_jwt_and_user_without_detached_session_error() -> None:
    auth_service.create_initial_admin_user_if_missing()

    response = client.post(
        "/api/auth/login",
        data={"username": "admin@jobcopilot.local", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@jobcopilot.local"
