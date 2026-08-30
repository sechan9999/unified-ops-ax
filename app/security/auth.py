"""Auth — resolve the caller's identity from a bearer token instead of a
request parameter (closes the 'role as request param' gap). role and
principals are derived server-side from the authenticated Employee."""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.domain.models import Employee
from app.security.rbac import principals_for

# OpenAPI Bearer Token Security Scheme for /docs Authorize Button
security_scheme = HTTPBearer(auto_error=False)


@dataclass
class Identity:
    employee_id: str
    name: str
    role: str
    principals: set[str]


def issue_token(session: Session, employee: Employee) -> str:
    token = secrets.token_urlsafe(24)
    employee.api_token = token
    session.commit()
    return token


def resolve_identity(session: Session, token: str) -> Identity:
    employee = session.scalar(select(Employee).where(Employee.api_token == token))
    if employee is None:
        raise HTTPException(401, "invalid token")
    return Identity(employee.id, employee.name, employee.role, principals_for(employee.role, employee.id))


def current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> Identity:
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]

    if not token:
        raise HTTPException(401, "missing bearer token")
    return resolve_identity(session, token)


def require_manager(identity: Identity = Depends(current_identity)) -> Identity:
    if identity.role != "manager":
        raise HTTPException(403, "manager role required")
    return identity


def require_bootstrap_or_manager(
    x_bootstrap_key: str | None = Header(default=None, alias="X-Bootstrap-Key"),
    authorization: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: Session = Depends(get_session),
) -> Identity | dict:
    settings = get_settings()
    if x_bootstrap_key and x_bootstrap_key == settings.admin_bootstrap_key:
        return {"bootstrap": True, "role": "manager"}

    # Fallback to manager identity check
    identity = current_identity(credentials=credentials, authorization=authorization, session=session)
    if identity.role != "manager":
        raise HTTPException(403, "manager authorization or bootstrap key required")
    return identity
