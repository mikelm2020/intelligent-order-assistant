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
