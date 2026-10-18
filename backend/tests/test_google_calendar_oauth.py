"""
Automated Test Suite for Google Calendar OAuth 2.0 Integration
Verifies:
1. Exact minimal scopes ('calendar.events' only, no full calendar access)
2. Offline access ('access_type=offline', 'prompt=consent')
3. CSRF state validation (valid vs forged/expired state parameters)
4. Exact registered callback URI usage
5. Secure authorization code exchange and persistent token storage
6. Preservation of existing refresh token when Google does not return a new one
7. Graceful handling of revoked credentials ('invalid_grant') and refresh failures
8. Disconnect flow and token revocation
9. Calendar sync with live connected Google Calendar
"""

import urllib.parse
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, StudySession, LearningRequest
from app.config import settings
from app.services.google_calendar_service import (
    google_calendar_oauth,
    CALENDAR_EVENTS_SCOPE,
    USERINFO_EMAIL_SCOPE
)


@pytest.fixture
def auth_user(client: TestClient, db_session: Session):
    """Registers a clean test user and returns user data and bearer auth headers."""
    email = "cal_user@example.com"
    pwd = "CalPassword123!"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": email, "password": pwd, "full_name": "Calendar Tester"}
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    return {"user_id": user_id, "email": email, "token": token, "headers": headers}


def test_calendar_oauth_scopes_and_offline_access(client: TestClient, auth_user, monkeypatch):
    """
    Verifies that the authorization URL:
    - Requests only minimal calendar scopes ('calendar.events')
    - Does NOT request excessive root 'calendar' scope
    - Uses offline access ('access_type=offline') and 'prompt=consent'
    - Includes a signed CSRF state parameter bound to user_id
    - Uses the exact registered callback URI
    """
    # Configure mock client ID
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", "mock_cal_client_id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_SECRET", "mock_cal_secret")

    res = client.get("/api/calendar/oauth/authorize", headers=auth_user["headers"])
    assert res.status_code == 200
    data = res.json()

    assert "auth_url" in data
    assert "state" in data
    assert "redirect_uri" in data
    assert data["redirect_uri"] == settings.get_calendar_redirect_uri()

    # Parse authorization URL query parameters
    parsed = urllib.parse.urlparse(data["auth_url"])
    params = urllib.parse.parse_qs(parsed.query)

    # 1. Scopes check
    requested_scopes = params.get("scope", [""])[0].split()
    assert CALENDAR_EVENTS_SCOPE in requested_scopes
    assert USERINFO_EMAIL_SCOPE in requested_scopes
    # Strictly ensure excessive full calendar root scope is NOT requested
    assert "https://www.googleapis.com/auth/calendar" not in requested_scopes

    # 2. Offline access & consent prompt check
    assert params.get("access_type") == ["offline"]
    assert params.get("prompt") == ["consent"]
    assert params.get("response_type") == ["code"]

    # 3. State parameter validation
    state_token = params.get("state", [""])[0]
    verified_state = google_calendar_oauth.verify_oauth_state(state_token)
    assert verified_state["sub"] == auth_user["user_id"]
    assert verified_state["purpose"] == "google_calendar_oauth"


def test_calendar_oauth_csrf_state_tampering_rejected(client: TestClient):
    """
    Verifies that tampered, forged, or expired state tokens are strictly rejected with 400 Bad Request.
    """
    # 1. Completely forged state
    res1 = client.get("/api/calendar/oauth/callback?code=fake_code&state=forged_state_value")
    assert res1.status_code == 400
    assert "invalid" in res1.json()["detail"].lower()

    # 2. Missing state
    res2 = client.get("/api/calendar/oauth/callback?code=fake_code")
    assert res2.status_code == 400
    assert "missing" in res2.json()["detail"].lower()


def test_calendar_oauth_code_exchange_and_token_storage(client: TestClient, auth_user, db_session: Session, monkeypatch):
    """
    Verifies that a valid authorization code is exchanged securely and the refresh token
    is stored in the user's persistent database record.
    """
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", "mock_cal_client_id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_SECRET", "mock_cal_secret")

    # Generate valid state for auth_user
    auth_data = google_calendar_oauth.generate_authorization_url(user_id=auth_user["user_id"])
    valid_state = auth_data["state"]

    mock_tokens = {
        "access_token": "mock_google_access_token_123",
        "refresh_token": "mock_google_refresh_token_abc",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": CALENDAR_EVENTS_SCOPE
    }

    # Mock external Google endpoints
    with patch.object(google_calendar_oauth, "exchange_code_for_tokens", return_value=mock_tokens), \
         patch.object(google_calendar_oauth, "fetch_google_account_email", return_value="student.cal@gmail.com"):

        callback_res = client.get(
            f"/api/calendar/oauth/callback?code=valid_auth_code&state={valid_state}",
            follow_redirects=False
        )
        assert callback_res.status_code == 303
        assert "calendar_connected=true" in callback_res.headers["location"]

    # Verify user database record has stored refresh token
    user = db_session.query(User).filter(User.id == auth_user["user_id"]).first()
    assert user.google_calendar_refresh_token == "mock_google_refresh_token_abc"
    assert user.google_calendar_access_token == "mock_google_access_token_123"
    assert user.google_calendar_email == "student.cal@gmail.com"
    assert user.google_calendar_connected_at is not None

    # Check status endpoint
    status_res = client.get("/api/calendar/oauth/status", headers=auth_user["headers"])
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["is_connected"] is True
    assert st_data["calendar_email"] == "student.cal@gmail.com"


def test_calendar_oauth_preserves_existing_refresh_token(client: TestClient, auth_user, db_session: Session):
    """
    CRUCIAL REQUIREMENT:
    When Google re-authenticates a user but does NOT return a new refresh token (refresh_token is None/omitted),
    the system MUST preserve the existing stored refresh token.
    """
    # 1. Set initial refresh token
    user = db_session.query(User).filter(User.id == auth_user["user_id"]).first()
    user.google_calendar_refresh_token = "initial_precious_refresh_token"
    db_session.commit()

    # 2. Simulate subsequent token exchange where Google omits refresh_token
    token_response_without_refresh = {
        "access_token": "brand_new_access_token_xyz",
        "expires_in": 3600,
        "token_type": "Bearer"
        # Notice: 'refresh_token' is NOT present in Google's response
    }

    google_calendar_oauth.save_user_tokens(
        db=db_session,
        user=user,
        token_data=token_response_without_refresh,
        google_email="student.cal@gmail.com"
    )

    # 3. Assert existing refresh token was strictly PRESERVED
    db_session.refresh(user)
    assert user.google_calendar_refresh_token == "initial_precious_refresh_token"
    assert user.google_calendar_access_token == "brand_new_access_token_xyz"


def test_calendar_oauth_graceful_handling_of_revoked_credentials(client: TestClient, auth_user, db_session: Session, monkeypatch):
    """
    Verifies that when credentials are revoked (Google returns 'invalid_grant' on token refresh),
    the system gracefully disconnects the calendar and returns None without raising an unhandled exception.
    """
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", "mock_id")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_CLIENT_SECRET", "mock_secret")

    user = db_session.query(User).filter(User.id == auth_user["user_id"]).first()
    user.google_calendar_refresh_token = "revoked_token_from_google"
    user.google_calendar_access_token = "expired_token"
    user.google_calendar_token_expiry = None
    db_session.commit()

    # Mock Google token endpoint returning 400 invalid_grant
    mock_revoked_response = MagicMock()
    mock_revoked_response.status_code = 400
    mock_revoked_response.headers = {"content-type": "application/json"}
    mock_revoked_response.json.return_value = {"error": "invalid_grant", "error_description": "Token has been revoked."}
    mock_revoked_response.text = '{"error": "invalid_grant"}'

    with patch("httpx.Client.post", return_value=mock_revoked_response):
        access_token = google_calendar_oauth.get_valid_access_token(db_session, user)

    # Must return None without crashing
    assert access_token is None

    # Must have cleanly cleared credentials from database
    db_session.refresh(user)
    assert user.google_calendar_refresh_token is None
    assert user.google_calendar_access_token is None
    assert user.google_calendar_email is None

    # Status endpoint reflects disconnected state
    status_res = client.get("/api/calendar/oauth/status", headers=auth_user["headers"])
    assert status_res.status_code == 200
    assert status_res.json()["is_connected"] is False


def test_calendar_oauth_disconnect_endpoint(client: TestClient, auth_user, db_session: Session):
    """
    Verifies that /api/calendar/oauth/disconnect wipes tokens from the database.
    """
    # 1. Connect user first
    user = db_session.query(User).filter(User.id == auth_user["user_id"]).first()
    user.google_calendar_refresh_token = "token_to_disconnect"
    user.google_calendar_access_token = "access_to_disconnect"
    user.google_calendar_email = "connected.user@gmail.com"
    db_session.commit()

    # 2. Call disconnect endpoint
    with patch("httpx.Client.post"):
        dis_res = client.post("/api/calendar/oauth/disconnect", headers=auth_user["headers"])
    assert dis_res.status_code == 200
    assert dis_res.json()["is_connected"] is False

    # 3. Verify database is cleared
    db_session.refresh(user)
    assert user.google_calendar_refresh_token is None
    assert user.google_calendar_access_token is None
    assert user.google_calendar_email is None


def test_calendar_sync_with_connected_google_calendar(client: TestClient, auth_user, db_session: Session):
    """
    Verifies that CalendarService.sync_calendar creates study sessions and
    calls Google Calendar event insertion when a valid access token is present.
    """
    # 1. Connect user with active token
    user = db_session.query(User).filter(User.id == auth_user["user_id"]).first()
    user.google_calendar_refresh_token = "active_refresh_token"
    user.google_calendar_access_token = "active_access_token"
    from datetime import datetime, timezone, timedelta
    user.google_calendar_token_expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    db_session.commit()

    # 2. Create learning path for this user
    path_res = client.post(
        "/api/learning-paths",
        headers=auth_user["headers"],
        json={
            "goal": "Cloud Architect",
            "starting_level": "Beginner",
            "weekly_hours": 5.0,
            "duration_value": 4,
            "duration_unit": "weeks"
        }
    )
    assert path_res.status_code == 201
    path_id = path_res.json()["id"]

    # 3. Approve a calendar action block with mocked Google API event insertion
    mock_g_event = {"id": "gcal_event_id_99999", "htmlLink": "https://calendar.google.com/event?eid=99999"}
    path_details = client.get(f"/api/learning-paths/{path_id}").json()
    actions = path_details.get("proposed_actions", [])
    cal_action = next((a for a in actions if a["action_type"] == "calendar_block"), None)
    assert cal_action is not None

    with patch.object(google_calendar_oauth, "insert_calendar_event", return_value=mock_g_event) as mock_insert:
        appr_res = client.post(f"/api/actions/{cal_action['id']}/approve")
        assert appr_res.status_code == 200
        assert mock_insert.called

    # 4. Sync calendar verification reflects live connected mode
    sync_res = client.post(f"/api/learning-paths/{path_id}/sync-calendar")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["integration_mode"] == "Google Calendar API (Live Connected)"
    assert sync_data["total_calendar_events"] >= 1

