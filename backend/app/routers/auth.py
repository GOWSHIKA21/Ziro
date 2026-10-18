"""
Authentication Router
Provides user registration, login, profile inspection, and session logout.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, utc_now
from ..schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from ..services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user with bcrypt password hashing and returns an access token.
    """
    # Check for duplicate account
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    # Hash password with bcrypt salt
    hashed_pwd = AuthService.hash_password(payload.password)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"

    new_user = User(
        id=user_id,
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name or payload.email.split("@")[0].capitalize(),
        is_active=True,
        created_at=utc_now()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue JWT token
    token = AuthService.create_access_token({"sub": new_user.id, "email": new_user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a JWT token.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not AuthService.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support."
        )

    token = AuthService.create_access_token({"sub": user.id, "email": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile information.
    """
    return user


@router.post("/logout")
def logout_user():
    """
    Stateless JWT client logout acknowledgment.
    """
    return {"message": "Logged out successfully. Client should discard stored token."}
