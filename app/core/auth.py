from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import User

settings = get_settings()
security = HTTPBearer()


class TokenData(BaseModel):
    user_id: int


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
    except JWTError:
        return None
    user = db.get(User, user_id)
    if user is None:
        return None
    return user
