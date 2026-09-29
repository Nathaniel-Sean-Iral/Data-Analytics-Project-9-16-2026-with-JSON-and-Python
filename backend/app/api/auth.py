from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_user, require_roles
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, TokenPair, User, UserCreate
from app.services.store import authenticate_user, create_user, get_user_by_username

router = APIRouter(tags=["auth"])

UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


def _user_payload(user_record: dict) -> User:
    return User(
        id=user_record["id"],
        username=user_record["username"],
        full_name=user_record["full_name"],
        role=user_record["role"],
        email=user_record.get("email"),
        is_active=user_record.get("is_active", True),
    )


def _issue_tokens(user_record: dict) -> dict:
    return {
        "access_token": create_access_token(user_record["username"], user_record["role"]),
        "refresh_token": create_refresh_token(user_record["username"], user_record["role"]),
        "token_type": "bearer",
    }


def _authenticate(username: str, password: str) -> dict:
    user_record = authenticate_user(username, password)
    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers=UNAUTHORIZED,
        )
    return {**_issue_tokens(user_record), "user": _user_payload(user_record).model_dump()}


@router.post("/auth/token", response_model=TokenPair, summary="OAuth2 password flow")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    return _authenticate(form_data.username, form_data.password)


@router.post("/auth/login", response_model=AuthResponse, summary="JSON login for the web client")
def login(payload: LoginRequest) -> dict:
    return _authenticate(payload.username, payload.password)


@router.post("/auth/refresh", response_model=TokenPair)
def refresh_tokens(payload: RefreshRequest) -> dict:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers=UNAUTHORIZED,
        ) from exc

    user_record = get_user_by_username(claims["sub"])
    if user_record is None or not user_record.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is no longer active",
            headers=UNAUTHORIZED,
        )
    return _issue_tokens(user_record)


@router.get("/auth/me", response_model=User)
def read_current_user(current_user: User = Depends(get_current_user)) -> dict:
    return current_user.model_dump()


@router.post("/auth/users", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    _admin: User = Depends(require_roles("admin")),
) -> dict:
    try:
        return create_user(payload.model_dump(), payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
