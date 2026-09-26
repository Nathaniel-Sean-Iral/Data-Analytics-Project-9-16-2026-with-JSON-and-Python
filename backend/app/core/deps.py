import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ROLE_RANK = {"viewer": 1, "responder": 2, "admin": 3}


def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise _credentials_exception()
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise _credentials_exception()
    except jwt.PyJWTError:
        raise _credentials_exception()

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise _credentials_exception()
    return user


def require_roles(*roles: str) -> User:
    """Role-gated dependency. Anyone with a rank >= the required role is allowed."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        # The least-privileged listed role defines the access floor (rank >= floor).
        allowed = min(ROLE_RANK[r] for r in roles)
        if ROLE_RANK.get(current_user.role, 0) < allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return checker