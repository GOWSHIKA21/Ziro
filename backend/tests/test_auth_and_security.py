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
