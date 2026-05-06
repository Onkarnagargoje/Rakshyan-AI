from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.utils.auth_deps import get_current_user
from app.utils.db import get_db
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User.id).where(User.email == str(payload.email)))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=str(payload.email), role="parent", password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(subject=user.email, extra={"role": user.role})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.email, extra={"role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return MeResponse(email=user.email, role=user.role)

