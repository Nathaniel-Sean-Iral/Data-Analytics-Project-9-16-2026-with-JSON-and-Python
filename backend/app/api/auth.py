from fastapi import APIRouter, HTTPException, status

from app.core.security import create_fake_token
from app.schemas import AuthResponse, LoginRequest, User
from app.services.store import USERS

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user_record = USERS.get(payload.username)
    if user_record is None or payload.password != "password":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = User(**user_record)
    return {
        "access_token": create_fake_token(payload.username),
        "token_type": "bearer",
        "user": user.model_dump(),
    }
