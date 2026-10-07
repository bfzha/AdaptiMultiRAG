from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.auth import router
from backend.service import auth


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_login_returns_token_and_user(monkeypatch):
    user = SimpleNamespace(
        id=7,
        username="alice",
        email="alice@example.com",
    )
    authenticate = AsyncMock(return_value=user)
    monkeypatch.setattr(auth, "authenticate_user", authenticate)
    monkeypatch.setattr(auth, "create_token", lambda data: f"token-for-{data['sub']}")

    response = client.post(
        "/auth/login",
        json={"email": " alice@example.com ", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": 200,
        "data": {
            "access_token": "token-for-7",
            "token_type": "bearer",
            "user": {
                "id": 7,
                "username": "alice",
                "email": "alice@example.com",
            },
        },
        "msg": None,
    }
    authenticate.assert_awaited_once_with(
        "alice@example.com",
        "correct-password",
    )


def test_login_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setattr(auth, "authenticate_user", AsyncMock(return_value=None))

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "邮箱或密码错误"}


def test_login_rejects_invalid_email_before_authentication(monkeypatch):
    authenticate = AsyncMock()
    monkeypatch.setattr(auth, "authenticate_user", authenticate)

    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "password"},
    )

    assert response.status_code == 422
    authenticate.assert_not_awaited()


def test_login_hides_internal_errors(monkeypatch):
    monkeypatch.setattr(
        auth,
        "authenticate_user",
        AsyncMock(side_effect=RuntimeError("database password leaked")),
    )

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "password"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "登录服务暂时不可用"}
    assert "database password leaked" not in response.text
