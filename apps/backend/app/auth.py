from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from apps.backend.app.models import UserRow
from apps.backend.app.persistence import session_scope
from apps.backend.app.config import settings


SECRET_KEY = os.getenv("JOBCOPILOT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JOBCOPILOT_ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class UserPublic(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class AuthService:
    def create_initial_admin_user_if_missing(self) -> None:
        with session_scope() as session:
            if session.query(UserRow).count():
                return
            user = UserRow(
                id=str(uuid4()),
                email=os.getenv("JOBCOPILOT_ADMIN_EMAIL", "admin@jobcopilot.local").lower(),
                hashed_password=self.hash_password(os.getenv("JOBCOPILOT_ADMIN_PASSWORD", "admin123")),
            )
            session.add(user)

    def hash_password(self, password: str) -> str:
        salt = os.getenv("JOBCOPILOT_PASSWORD_SALT", "jobcopilot-salt").encode("utf-8")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return digest.hex()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return hmac.compare_digest(self.hash_password(password), hashed_password)

    def authenticate(self, email: str, password: str) -> UserRow:
        with session_scope() as session:
            user = session.query(UserRow).filter(UserRow.email == email.lower()).one_or_none()
            if user is None or not self.verify_password(password, user.hashed_password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            return user

    def create_access_token(self, user: UserRow) -> str:
        expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": user.id, "email": user.email, "exp": expires}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def login(self, form: OAuth2PasswordRequestForm) -> TokenResponse:
        user = self.authenticate(form.username, form.password)
        token = self.create_access_token(user)
        return TokenResponse(
            access_token=token,
            user=UserPublic(id=UUID(user.id), email=user.email, created_at=user.created_at),
        )


auth_service = AuthService()


def decode_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def current_user(token: Annotated[str | None, Depends(oauth2_scheme)]) -> UserPublic:
    if not token and settings.app_env != "production":
        auth_service.create_initial_admin_user_if_missing()
        with session_scope() as session:
            user = session.query(UserRow).filter(UserRow.email == os.getenv("JOBCOPILOT_ADMIN_EMAIL", "admin@jobcopilot.local").lower()).one()
            return UserPublic(id=UUID(user.id), email=user.email, created_at=user.created_at)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    with session_scope() as session:
        user = session.get(UserRow, str(user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return UserPublic(id=UUID(user.id), email=user.email, created_at=user.created_at)
