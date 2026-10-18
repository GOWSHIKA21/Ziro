"""
Google Calendar OAuth 2.0 Service
Handles:
- Scoped authorization URL generation (minimal 'calendar.events' scope + offline access)
- Cryptographic state parameter creation & CSRF validation
- Secure authorization code exchange
- Refresh token persistence with preservation when Google omits a new one
- Automatic token refresh & graceful handling of revoked credentials ('invalid_grant')
- Calendar disconnection & token revocation
- Live Google Calendar event insertion with mock calendar fallback
"""

import uuid
import urllib.parse
import datetime
import logging
from typing import Dict, Any, Optional

import jwt
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, utc_now

logger = logging.getLogger("google_calendar_oauth")

# Exact minimal scopes needed for creating and managing study session events
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"
USERINFO_EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarOAuthService:
    def __init__(self):
        self.scope = f"{CALENDAR_EVENTS_SCOPE} {USERINFO_EMAIL_SCOPE}"

    def is_configured(self) -> bool:
        """Checks if Google Calendar OAuth client credentials are configured."""
        client_id = settings.get_calendar_client_id()
        client_secret = settings.get_calendar_client_secret()
        return bool(client_id and client_secret and len(client_id) > 5)

    def generate_authorization_url(self, user_id: str, redirect_to: Optional[str] = None) -> Dict[str, str]:
        """
        Builds the Google OAuth 2.0 authorization URL with:
        - Exact minimal scope: 'https://www.googleapis.com/auth/calendar.events'
        - Offline access (access_type=offline)
        - Force consent prompt (prompt=consent) to guarantee refresh_token generation
        - Cryptographic signed state token to prevent CSRF and session hijacking
        - Exact registered callback URI
        """
        client_id = settings.get_calendar_client_id()
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Calendar Client ID is not configured. Please set GOOGLE_CALENDAR_CLIENT_ID or GOOGLE_OAUTH_CLIENT_ID."
            )

        redirect_uri = settings.get_calendar_redirect_uri()

        # Generate tamper-proof state token (valid for 15 minutes)
        state_payload = {
            "sub": user_id,
            "nonce": uuid.uuid4().hex,
            "purpose": "google_calendar_oauth",
            "redirect_to": redirect_to or "",
            "exp": utc_now() + datetime.timedelta(minutes=15)
        }
        state_token = jwt.encode(state_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "access_type": "offline",           # Required to receive a refresh_token
            "prompt": "consent",                 # Forces consent screen to ensure refresh_token is returned
            "include_granted_scopes": "true",
            "state": state_token
        }

        auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return {
            "auth_url": auth_url,
            "state": state_token,
            "redirect_uri": redirect_uri,
            "scope": self.scope
        }

    def verify_oauth_state(self, state: str) -> Dict[str, Any]:
        """
        Validates the incoming OAuth state parameter against CSRF attacks.
        Checks signature, expiration, and OAuth purpose.
        """
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing OAuth state parameter."
            )

        try:
            payload = jwt.decode(
                state,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("purpose") != "google_calendar_oauth":
                raise ValueError("Invalid OAuth purpose.")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state parameter has expired. Please initiate calendar authorization again."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OAuth state parameter: {str(e)}"
            )

    def exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Securely exchanges the authorization code for access and refresh tokens.
        Uses the exact registered redirect URI.
        """
        client_id = settings.get_calendar_client_id()
        client_secret = settings.get_calendar_client_secret()
        reg_redirect_uri = redirect_uri or settings.get_calendar_redirect_uri()

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Calendar OAuth client credentials are not configured on server."
            )

        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": reg_redirect_uri,
            "grant_type": "authorization_code"
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(GOOGLE_TOKEN_URL, data=token_data)
                
            if res.status_code != 200:
                err_body = res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text
                logger.error(f"Google token exchange failed ({res.status_code}): {err_body}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google token exchange failed: {err_body}"
                )

            return res.json()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exception during Google token exchange: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Network error communicating with Google token endpoint: {str(e)}"
            )

    def fetch_google_account_email(self, access_token: str) -> Optional[str]:
        """Fetches the Google account email associated with the token for UI display."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            if res.status_code == 200:
                data = res.json()
                return data.get("email")
        except Exception as e:
            logger.warning(f"Could not fetch Google userinfo email: {e}")
        return None

    def save_user_tokens(
        self,
        db: Session,
        user: User,
        token_data: Dict[str, Any],
        google_email: Optional[str] = None
    ) -> User:
        """
        Stores tokens securely in persistent backend database.
        PRESERVES existing refresh token if Google does not return a new one.
        """
        access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        granted_scope = token_data.get("scope", self.scope)

        # 1. Update short-lived access token & expiry
        user.google_calendar_access_token = access_token
        user.google_calendar_token_expiry = utc_now() + datetime.timedelta(seconds=expires_in - 60)

        # 2. Preserve existing refresh token when Google does not return a new one
        if new_refresh_token:
            user.google_calendar_refresh_token = new_refresh_token
            logger.info(f"Updated refresh token for user {user.id}")
        elif user.google_calendar_refresh_token:
            logger.info(f"Preserving existing refresh token for user {user.id} as Google omitted a new one")

        # 3. Save connection metadata
        if google_email:
            user.google_calendar_email = google_email
        user.google_calendar_connected_at = utc_now()
        user.google_calendar_scope = granted_scope

        db.commit()
        db.refresh(user)
        return user

    def get_valid_access_token(self, db: Session, user: User) -> Optional[str]:
        """
        Returns a valid, non-expired access token.
        Automatically refreshes if expired.
        Gracefully handles revoked credentials ('invalid_grant') by disconnecting without crashing.
        """
        if not user.google_calendar_refresh_token:
            return None

        # Check if current access token is still fresh
        if user.google_calendar_access_token and user.google_calendar_token_expiry:
            if user.google_calendar_token_expiry > utc_now():
                return user.google_calendar_access_token

        # Access token is expired or missing -> Refresh it
        return self.refresh_access_token(db, user)

    def refresh_access_token(self, db: Session, user: User) -> Optional[str]:
        """
        Refreshes access token using stored refresh token.
        If credentials were revoked ('invalid_grant'), cleanly disconnects user's calendar.
        """
        refresh_token = user.google_calendar_refresh_token
        if not refresh_token:
            return None

        client_id = settings.get_calendar_client_id()
        client_secret = settings.get_calendar_client_secret()

        if not client_id or not client_secret:
            logger.warning("Cannot refresh calendar access token: client credentials missing.")
            return None

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(GOOGLE_TOKEN_URL, data=payload)

            if res.status_code == 200:
                data = res.json()
                new_access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                new_refresh_token = data.get("refresh_token")

                user.google_calendar_access_token = new_access_token
                user.google_calendar_token_expiry = utc_now() + datetime.timedelta(seconds=expires_in - 60)

                # Preserve existing refresh token if not returned
                if new_refresh_token:
                    user.google_calendar_refresh_token = new_refresh_token

                db.commit()
                db.refresh(user)
                return new_access_token

            # Handle revoked credentials or expired refresh tokens
            err_data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            error_code = err_data.get("error", "")

            if res.status_code in [400, 401] and error_code in ["invalid_grant", "unauthorized_client"]:
                logger.warning(
                    f"Google Calendar credentials for user {user.id} were revoked or invalid ({error_code}). "
                    "Gracefully disconnecting calendar."
                )
                self.disconnect_calendar(db, user, revoke_at_google=False)
                return None

            logger.error(f"Failed to refresh Google Calendar token ({res.status_code}): {res.text}")
            return None

        except Exception as e:
            logger.error(f"Error during Google Calendar token refresh for user {user.id}: {str(e)}")
            return None

    def disconnect_calendar(self, db: Session, user: User, revoke_at_google: bool = True) -> Dict[str, Any]:
        """
        Disconnects a user's Google Calendar and wipes stored tokens from persistent database.
        Optionally revokes the token at Google's revocation endpoint.
        """
        token_to_revoke = user.google_calendar_refresh_token or user.google_calendar_access_token

        if revoke_at_google and token_to_revoke:
            try:
                with httpx.Client(timeout=5.0) as client:
                    client.post(GOOGLE_REVOKE_URL, params={"token": token_to_revoke})
            except Exception as e:
                logger.warning(f"Could not revoke token with Google during disconnect: {e}")

        # Wipe persistent storage on user record
        user.google_calendar_refresh_token = None
        user.google_calendar_access_token = None
        user.google_calendar_token_expiry = None
        user.google_calendar_email = None
        user.google_calendar_connected_at = None
        user.google_calendar_scope = None

        db.commit()
        db.refresh(user)

        return {
            "message": "Google Calendar disconnected successfully.",
            "is_connected": False
        }

    def insert_calendar_event(
        self,
        access_token: str,
        title: str,
        start_datetime_iso: str,
        end_datetime_iso: str,
        description: str = "",
        location: str = "Online / Self-Paced"
    ) -> Dict[str, Any]:
        """
        Inserts an event into the user's primary Google Calendar via Google Calendar API v3.
        """
        event_body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_datetime_iso,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_datetime_iso,
                "timeZone": "UTC"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "email", "minutes": 60}
                ]
            }
        }

        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events"
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                url,
                json=event_body,
                headers={"Authorization": f"Bearer {access_token}"}
            )

        if res.status_code in [200, 201]:
            return res.json()
        
        raise RuntimeError(f"Google Calendar API insert failed ({res.status_code}): {res.text}")


google_calendar_oauth = GoogleCalendarOAuthService()
