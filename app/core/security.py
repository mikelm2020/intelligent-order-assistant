from dataclasses import dataclass
from secrets import compare_digest
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    role: Literal["operator", "reviewer"]


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Principal:
    if not settings.operator_api_key or not settings.reviewer_api_key:
        raise HTTPException(503, "API credentials are not configured")
    if credentials is None:
        raise HTTPException(
            401, "Bearer credentials required", headers={"WWW-Authenticate": "Bearer"}
        )
    for role, key in (
        ("operator", settings.operator_api_key),
        ("reviewer", settings.reviewer_api_key),
    ):
        if compare_digest(
            credentials.credentials.encode(), key.get_secret_value().encode()
        ):
            return Principal(role=role)
    raise HTTPException(
        401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}
    )


PrincipalDep = Annotated[Principal, Depends(get_principal)]


async def require_reviewer(principal: PrincipalDep) -> Principal:
    if principal.role != "reviewer":
        raise HTTPException(403, "Reviewer approval required")
    return principal


ReviewerDep = Annotated[Principal, Depends(require_reviewer)]
