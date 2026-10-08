import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, settings
from app.core.security import Principal, get_principal, require_reviewer


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["operator", "reviewer"])
async def test_roles_are_derived_from_server_credentials(role):
    key = getattr(settings, f"{role}_api_key").get_secret_value()
    principal = await get_principal(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=key)
    )
    assert principal.role == role


@pytest.mark.asyncio
async def test_operator_cannot_approve():
    with pytest.raises(HTTPException) as error:
        await require_reviewer(Principal("operator"))
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "operator_api_key", None)
    with pytest.raises(HTTPException) as error:
        await get_principal(None)
    assert error.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("token", ["invalid", "credencial-ñ"])
async def test_invalid_credentials_return_401(token):
    with pytest.raises(HTTPException) as error:
        await get_principal(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        )
    assert error.value.status_code == 401


def test_same_credentials_are_rejected():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://localhost/test",
            operator_api_key=SecretStr("a" * 32),
            reviewer_api_key=SecretStr("a" * 32),
        )


def test_missing_ai_credentials_return_sanitized_error(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "ai_provider", "openai")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/documents",
            headers={
                "Authorization": "Bearer "
                + settings.operator_api_key.get_secret_value()
            },
            json={"title": "Document", "content": "Demo"},
        )
    assert response.status_code == 503
    assert response.json() == {"detail": "AI provider credentials are not configured"}
