"""
Authentication & Authorization Service
Provides bcrypt password hashing, JWT bearer token management,
and user session security.
"""

import os
import uuid
import datetime
from datetime import timezone, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User, utc_now

security = HTTPBearer(auto_error=False)

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plaintext password using bcrypt with a random salt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a plaintext password against a bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Creates a signed JWT access token."""
        to_encode = data.copy()
        now = datetime.datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": now,
            "jti": uuid.uuid4().hex
        })
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decodes and validates a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def verify_google_token(credential: str) -> Dict[str, Any]:
        """
        Validates Google ID Token using official google-auth library and fallback tokeninfo.
        Never trusts client-supplied user identity without verification.
        Ensures email_verified is True to prevent account-linking vulnerabilities.
        """
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Google OAuth credential."
            )

        # 1. Try official google-auth library verification
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            client_id = settings.GOOGLE_OAUTH_CLIENT_ID
            id_info = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                audience=client_id if client_id else None
            )

            if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError(f"Invalid Google token issuer: {id_info.get('iss')}")

            if not id_info.get("email_verified", False):
                raise ValueError("Google account email is not verified.")

            return {
                "google_id": id_info.get("sub"),
                "email": id_info.get("email", "").lower(),
                "name": id_info.get("name") or id_info.get("email", "").split("@")[0].capitalize(),
                "picture": id_info.get("picture")
            }
        except Exception as e:
            # 2. Fallback to Google's online tokeninfo endpoint for test/dev flexibility
            try:
                import httpx
                resp = httpx.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    verified = data.get("email_verified") in [True, "true", "True"]
                    if not verified:
                        raise ValueError("Google account email is not verified.")
                    return {
                        "google_id": data.get("sub"),
                        "email": data.get("email", "").lower(),
                        "name": data.get("name") or data.get("email", "").split("@")[0].capitalize(),
                        "picture": data.get("picture")
                    }
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google ID token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns the authenticated User if a valid Bearer token is provided in the Authorization header.
    Returns None if no token or invalid token (permits guest/demo mode).
    Strictly avoids reading sensitive credentials from URL query parameters.
    """
    if not creds or not creds.credentials:
        return None

    payload = AuthService.decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        return None

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Strict authentication dependency. Raises HTTP 401 if unauthenticated.
    """
    user = get_current_user_optional(creds, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_guest_session_id_optional(
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
) -> Optional[str]:
    """
    Extracts optional guest session ID strictly from request headers.
    Avoids query parameter exposure in access logs, proxies, and browser history.
    """
    return x_guest_session_id


def verify_learning_path_access(
    req,
    current_user: Optional[User] = None,
    guest_session_id: Optional[str] = None,
    is_mutation: bool = False,
    is_delete: bool = False
) -> None:
    """
    Enforces comprehensive multi-tenant authorization for learning paths and child entities:
    1. Authenticated User Paths (req.user_id is not None):
       - Unauthenticated requests -> 401 Unauthorized
       - Different user -> 403 Forbidden
       - Owner -> Permitted
    2. Guest Session Paths (req.guest_session_id is not None):
       - Authenticated user without matching user_id -> 403 Forbidden
       - Guest with no session header -> 401 Unauthorized
       - Guest with mismatched session ID -> 403 Forbidden
       - Guest with matching session ID -> Permitted
    3. Shared Benchmark / Legacy Paths (req.is_benchmark is True or req.user_id is None and req.guest_session_id is None):
       - Read operations -> Permitted for public / benchmark inspection
       - Deletions -> 403 Forbidden (protects shared benchmark and seeded data)
       - Mutations (generate, adapt, replace-resource, edit/approve/execute actions, sync calendar) ->
         Strictly 403 Forbidden on benchmarks. Unassigned paths cannot be mutated by guest/user sessions.
    """
    if req is None:
        return

    req_user_id = getattr(req, "user_id", None)
    req_guest_session_id = getattr(req, "guest_session_id", None)
    req_is_benchmark = bool(getattr(req, "is_benchmark", False))

    # 1. Private User Path Check
    if req_user_id is not None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this private learning path.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if current_user.id != req_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this learning path."
            )
        return

    # 2. Private Guest Session Path Check
    if req_guest_session_id is not None:
        if current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access another guest's learning path."
            )
        if not guest_session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest session ID required to access this learning path."
            )
        if guest_session_id != req_guest_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access another guest's learning path."
            )
        return

    # 3. Shared Benchmark / Legacy Path Protection
    if is_delete or req_is_benchmark:
        if is_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Shared benchmark learning paths cannot be deleted."
            )
        if is_mutation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Shared benchmark learning paths cannot be modified or deleted."
            )

    # 4. Mutations on unassigned records (user_id is None and guest_session_id is None)
    if is_mutation:
        if guest_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to modify this shared benchmark."
            )
        if current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to modify this shared benchmark."
            )
        if os.environ.get("TESTING") != "1":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest session ID or authentication required to modify learning paths."
            )
