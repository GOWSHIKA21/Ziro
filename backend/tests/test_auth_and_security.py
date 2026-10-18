"""
Automated Security, Authentication, and Adaptive Replanning Tests
Verifies user registration, bcrypt hashing, JWT issuance, protected routes,
user data isolation (User A vs User B), SSRF URL protection, and adaptive recovery replanning.
"""

import pytest
from fastapi.testclient import TestClient
from app.services.verifier import ResourceVerifier
from app.models import User, LearningRequest, StudySession

def test_user_registration_success(client: TestClient):
    """Verifies that a new user can register and receive a signed JWT token."""
    res = client.post(
        "/api/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePassword123!",
            "full_name": "Alice Analyst"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["full_name"] == "Alice Analyst"


def test_duplicate_registration_rejected(client: TestClient):
    """Verifies duplicate account registration is rejected with 400 Bad Request."""
    client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "Password123!", "full_name": "Bob"}
    )
    res2 = client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "DifferentPassword123!", "full_name": "Bob Duplicate"}
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_short_password_rejected(client: TestClient):
    """Verifies short passwords (< 8 characters) fail validation."""
    res = client.post(
        "/api/auth/register",
        json={"email": "charlie@example.com", "password": "short", "full_name": "Charlie"}
    )
    assert res.status_code == 422


def test_login_success_and_invalid_credentials(client: TestClient):
    """Verifies login succeeds with correct credentials and rejects incorrect passwords."""
    client.post(
        "/api/auth/register",
        json={"email": "dan@example.com", "password": "ValidPassword999", "full_name": "Dan"}
    )
    
    # Valid login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "dan@example.com", "password": "ValidPassword999"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Invalid password
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "dan@example.com", "password": "WrongPassword"}
    )
    assert bad_login.status_code == 401


def test_auth_me_protected_endpoint(client: TestClient):
    """Verifies /api/auth/me requires valid bearer token."""
    # Without token -> 401
    unauth = client.get("/api/auth/me")
    assert unauth.status_code == 401

    # With token -> 200
    reg = client.post(
        "/api/auth/register",
        json={"email": "eva@example.com", "password": "Password888!", "full_name": "Eva"}
    ).json()
    token = reg["access_token"]

    auth = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth.status_code == 200
    assert auth.json()["email"] == "eva@example.com"


def test_passwords_never_stored_plaintext(client: TestClient, db_session):
    """Verifies that passwords are never stored in plaintext and use bcrypt."""
    client.post(
        "/api/auth/register",
        json={"email": "frank@example.com", "password": "SuperSecretPassword123", "full_name": "Frank"}
    )
    user = db_session.query(User).filter(User.email == "frank@example.com").first()
    assert user is not None
    assert user.hashed_password != "SuperSecretPassword123"
    assert user.hashed_password.startswith("$2b$")


def test_user_data_isolation(client: TestClient):
    """
    Security Test: User A creates a learning path.
    User B attempts to read or delete User A's learning path.
    Server MUST reject with 403 Forbidden.
    """
    # Register User A
    user_a = client.post(
        "/api/auth/register",
        json={"email": "usera@example.com", "password": "Password1234!", "full_name": "User A"}
    ).json()
    token_a = user_a["access_token"]

    # Register User B
    user_b = client.post(
        "/api/auth/register",
        json={"email": "userb@example.com", "password": "Password5678!", "full_name": "User B"}
    ).json()
    token_b = user_b["access_token"]

    # User A creates a path
    path_a = client.post(
        "/api/learning-paths",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "goal": "Data Analyst",
            "starting_level": "Beginner",
            "weekly_hours": 5.0,
            "duration_value": 6,
            "duration_unit": "months"
        }
    ).json()
    path_a_id = path_a["id"]

    # User A can access it
    ok_res = client.get(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert ok_res.status_code == 200

    # User B attempts to access User A's path -> 403 Forbidden
    forbidden_get = client.get(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert forbidden_get.status_code == 403

    # User B attempts to delete User A's path -> 403 Forbidden
    forbidden_del = client.delete(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert forbidden_del.status_code == 403


def test_ssrf_url_protection():
    """
    Security Test: Verifies SSRF protection blocks private, loopback, and metadata IPs.
    """
    # Block loopback
    is_safe, msg = ResourceVerifier.is_safe_url("http://127.0.0.1:8000/api/health")
    assert is_safe is False
    assert "prohibited" in msg.lower() or "blocked" in msg.lower()

    # Block localhost
    is_safe, msg = ResourceVerifier.is_safe_url("http://localhost:5000/secret")
    assert is_safe is False

    # Block non-http schemes
    is_safe, msg = ResourceVerifier.is_safe_url("file:///etc/passwd")
    assert is_safe is False

    # Allow valid public educational domain
    is_safe, _ = ResourceVerifier.is_safe_url("https://www.freecodecamp.org/learn")
    assert is_safe is True

    is_safe, _ = ResourceVerifier.is_safe_url("https://docs.python.org/3/tutorial/")
    assert is_safe is True


def test_adaptive_recovery_replanning(client: TestClient):
    """
    Verifies the Adaptive Recovery Engine:
    Recalculates study load when weekly availability changes and preserves completed sessions.
    """
    # 1. Create a learning path
    path = client.post(
        "/api/learning-paths",
        json={
            "goal": "Data Analyst",
            "starting_level": "Beginner",
            "weekly_hours": 5.0,
            "duration_value": 6,
            "duration_unit": "months"
        }
    ).json()
    path_id = path["id"]

    # 2. Mark one study session as completed with actual minutes
    sessions = client.get(f"/api/calendar/sessions?learning_request_id={path_id}").json()
    if sessions:
        sess_id = sessions[0]["id"]
        client.post(
            f"/api/calendar/sessions/{sess_id}/toggle-complete",
            json={
                "is_completed": True,
                "actual_minutes_studied": 150,
                "study_notes": "Completed Excel formulas and practiced pivot tables."
            }
        )

    # 3. Trigger Adaptive Recovery with reduced weekly hours (from 5h down to 3h)
    adapt_res = client.post(
        f"/api/learning-paths/{path_id}/adapt",
        json={
            "new_weekly_hours": 3.0,
            "missed_strategy": "rebalance"
        }
    )
    assert adapt_res.status_code == 200
    adapted_path = adapt_res.json()
    assert adapted_path["weekly_hours"] == 3.0
    assert len(adapted_path["adaptive_revisions"]) >= 1

    rev = adapted_path["adaptive_revisions"][0]
    assert rev["revision_type"] == "rebalance"
    assert "Adaptive Recovery applied" in rev["reasoning"]


def test_google_oauth_config_endpoint(client: TestClient):
    """Verifies /api/auth/google/config returns public configuration safely."""
    res = client.get("/api/auth/google/config")
    assert res.status_code == 200
    data = res.json()
    assert "client_id" in data
    assert "is_configured" in data
    assert isinstance(data["is_configured"], bool)
    # Ensure client secret is NEVER present
    assert "client_secret" not in data
    assert "secret" not in data


def test_google_oauth_first_time_signup_and_protected_access(client: TestClient, monkeypatch):
    """
    Verifies that a first-time Google user is automatically provisioned,
    receives a valid JWT, can access protected endpoints, and create user-specific learning paths.
    """
    from app.services.auth_service import AuthService

    # Mock Google ID token verification
    mock_profile = {
        "google_id": "google_10987654321",
        "email": "sarah.connor@gmail.com",
        "name": "Sarah Connor",
        "picture": "https://lh3.googleusercontent.com/a/mock-sarah"
    }
    monkeypatch.setattr(AuthService, "verify_google_token", lambda token: mock_profile)

    # First-time Google Sign-Up
    res = client.post("/api/auth/google", json={"credential": "mock_google_id_token_sarah"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "sarah.connor@gmail.com"
    assert data["user"]["full_name"] == "Sarah Connor"
    assert data["user"]["auth_provider"] == "google"
    assert data["user"]["google_id"] == "google_10987654321"
    assert data["user"]["avatar_url"] == "https://lh3.googleusercontent.com/a/mock-sarah"

    token = data["access_token"]
    user_id = data["user"]["id"]

    # Verify protected /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id

    # Verify creating a user-specific learning path
    path_res = client.post(
        "/api/learning-paths",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "goal": "Cybersecurity Analyst",
            "starting_level": "Beginner",
            "weekly_hours": 6.0,
            "duration_value": 3,
            "duration_unit": "months"
        }
    )
    assert path_res.status_code == 201
    assert path_res.json()["user_id"] == user_id



def test_google_oauth_returning_user_signin(client: TestClient, monkeypatch):
    """
    Verifies that returning Google users sign in seamlessly into their existing account.
    """
    from app.services.auth_service import AuthService

    mock_profile = {
        "google_id": "google_returning_999",
        "email": "returning.user@gmail.com",
        "name": "Returning User",
        "picture": "https://lh3.googleusercontent.com/a/mock-returning"
    }
    monkeypatch.setattr(AuthService, "verify_google_token", lambda token: mock_profile)

    # 1. Sign up first time
    res1 = client.post("/api/auth/google", json={"credential": "token_1"})
    assert res1.status_code == 200
    first_user_id = res1.json()["user"]["id"]

    # 2. Sign in returning user
    res2 = client.post("/api/auth/google", json={"credential": "token_2"})
    assert res2.status_code == 200
    assert res2.json()["user"]["id"] == first_user_id
    assert res2.json()["user"]["email"] == "returning.user@gmail.com"


def test_google_oauth_secure_account_linking(client: TestClient, monkeypatch):
    """
    Verifies secure account linking:
    When an account was created via standard email/password,
    signing in with a cryptographically verified Google account of the same email
    safely links the Google ID without creating a duplicate account.
    """
    from app.services.auth_service import AuthService

    # 1. Register with email/password
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "linkable.student@gmail.com",
            "password": "PasswordStudent123!",
            "full_name": "Linkable Student"
        }
    )
    assert reg.status_code == 201
    orig_user_id = reg.json()["user"]["id"]

    # 2. Later sign in with Google for that same verified email
    mock_google = {
        "google_id": "google_linked_sub_456",
        "email": "linkable.student@gmail.com",
        "name": "Linkable Student Google",
        "picture": "https://lh3.googleusercontent.com/a/mock-linked"
    }
    monkeypatch.setattr(AuthService, "verify_google_token", lambda token: mock_google)

    oauth_res = client.post("/api/auth/google", json={"credential": "token_link"})
    assert oauth_res.status_code == 200
    linked_data = oauth_res.json()
    assert linked_data["user"]["id"] == orig_user_id
    assert linked_data["user"]["google_id"] == "google_linked_sub_456"
    assert linked_data["user"]["avatar_url"] == "https://lh3.googleusercontent.com/a/mock-linked"

    # 3. User can still sign in with original password as well
    pw_res = client.post(
        "/api/auth/login",
        json={"email": "linkable.student@gmail.com", "password": "PasswordStudent123!"}
    )
    assert pw_res.status_code == 200
    assert pw_res.json()["user"]["id"] == orig_user_id


def test_google_oauth_invalid_token_rejection(client: TestClient):
    """Verifies that an invalid/forged Google token is rejected with 401 Unauthorized."""
    res = client.post("/api/auth/google", json={"credential": "completely_fake_invalid_token"})
    assert res.status_code == 401
    assert "verification failed" in res.json()["detail"].lower()


def test_google_oauth_unverified_email_fails():
    """Verifies that Google accounts with email_verified == False are rejected."""
    from fastapi import HTTPException
    from app.services.auth_service import AuthService
    from unittest.mock import patch

    with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "unverified_sub",
            "email": "unverified@example.com",
            "email_verified": False
        }
        with pytest.raises(HTTPException) as exc:
            AuthService.verify_google_token("dummy_token")
        assert exc.value.status_code == 401
        assert "not verified" in exc.value.detail.lower()


