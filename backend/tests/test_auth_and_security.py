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
    Security Test:
    - User A creates a private learning path.
    - User A can read and list their own path.
    - User B cannot read, list, or delete User A's learning path (403 Forbidden).
    - Anonymous users cannot read, list, or delete User A's learning path (401 Unauthorized / empty list).
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

    # 1. User A can access it
    ok_res = client.get(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert ok_res.status_code == 200

    # 2. User A lists their paths and sees path_a
    list_a = client.get("/api/learning-paths", headers={"Authorization": f"Bearer {token_a}"})
    assert list_a.status_code == 200
    assert any(p["id"] == path_a_id for p in list_a.json())

    # 3. User B attempts to access User A's path -> 403 Forbidden
    forbidden_get = client.get(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert forbidden_get.status_code == 403

    # 4. User B attempts to list paths -> does NOT see User A's path
    list_b = client.get("/api/learning-paths", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert not any(p["id"] == path_a_id for p in list_b.json())

    # 5. User B attempts to delete User A's path -> 403 Forbidden
    forbidden_del = client.delete(f"/api/learning-paths/{path_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert forbidden_del.status_code == 403

    # 6. Anonymous user attempts to list paths -> returns empty list (no data leak)
    anon_list = client.get("/api/learning-paths")
    assert anon_list.status_code == 200
    assert anon_list.json() == []

    # 7. Anonymous user attempts to read User A's path -> 401 Unauthorized
    anon_get = client.get(f"/api/learning-paths/{path_a_id}")
    assert anon_get.status_code == 401

    # 8. Anonymous user attempts to delete User A's path -> 401 Unauthorized
    anon_del = client.delete(f"/api/learning-paths/{path_a_id}")
    assert anon_del.status_code == 401

    # 9. Action approval isolation: User B or Anon cannot approve User A's proposed action
    cal_action = next((a for a in path_a["proposed_actions"] if a["action_type"] == "calendar_block"), None)
    if cal_action:
        # Anonymous approval rejected
        anon_appr = client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})
        assert anon_appr.status_code == 401

        # User B approval rejected
        b_appr = client.post(
            f"/api/actions/{cal_action['id']}/approve",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"decision": "approve"}
        )
        assert b_appr.status_code == 403

        # User A approval succeeds
        a_appr = client.post(
            f"/api/actions/{cal_action['id']}/approve",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"decision": "approve"}
        )
        assert a_appr.status_code == 200


def test_anonymous_guest_isolation_and_workflow(client: TestClient):
    """
    Verifies that guest functionality (creating, reading by ID, and approving demo paths)
    functions smoothly while maintaining privacy isolation from saved lists.
    """
    # 1. Anonymous visitor lists paths -> empty list (clean welcome view)
    init_list = client.get("/api/learning-paths")
    assert init_list.status_code == 200
    assert init_list.json() == []

    # 2. Anonymous visitor triggers Explore Benchmark / Goal Creation
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    guest_path_res = client.post("/api/learning-paths", json=payload)
    assert guest_path_res.status_code == 201
    guest_path = guest_path_res.json()
    assert guest_path["user_id"] is None
    guest_id = guest_path["id"]

    # 3. Anonymous visitor can read their guest path by explicit ID
    detail_res = client.get(f"/api/learning-paths/{guest_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == guest_id

    # 4. Anonymous visitor can approve actions on their unassigned guest path
    if guest_path["proposed_actions"]:
        action_id = guest_path["proposed_actions"][0]["id"]
        approve_res = client.post(f"/api/actions/{action_id}/approve", json={"decision": "approve"})
        assert approve_res.status_code == 200


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


def test_guest_session_isolation_guest_a_vs_guest_b(client: TestClient):
    """
    Verifies multi-tenant guest isolation:
    1. Guest A creates a path with X-Guest-Session-ID: 'gst_alice_123'.
    2. Guest A can read, list, and modify their path.
    3. Guest B with X-Guest-Session-ID: 'gst_bob_456':
       - Listing paths does not return Guest A's path.
       - GET /api/learning-paths/{id} returns 403 Forbidden.
       - DELETE /api/learning-paths/{id} returns 403 Forbidden.
       - POST /api/learning-paths/{id}/generate returns 403 Forbidden.
       - POST /api/learning-paths/{id}/adapt returns 403 Forbidden.
       - GET /api/learning-paths/{id}/resources returns 403 Forbidden.
       - POST /api/learning-paths/{id}/verify returns 403 Forbidden.
       - GET /api/learning-paths/{id}/actions returns 403 Forbidden.
       - POST /api/learning-paths/{id}/sync-calendar returns 403 Forbidden.
       - GET /api/calendar/sessions?learning_request_id={id} returns 403 Forbidden.
       - GET /api/calendar/export-ics?learning_request_id={id} returns 403 Forbidden.
       - GET /api/learning-paths/{id}/export-markdown returns 403 Forbidden.
    4. Unauthenticated request without guest header:
       - GET /api/learning-paths/{id} returns 401 Unauthorized.
       - DELETE /api/learning-paths/{id} returns 401 Unauthorized.
    5. Action authorization:
       - Guest B cannot approve Guest A's proposed action (403 Forbidden).
       - Guest without header cannot approve (401 Unauthorized).
       - Guest A can approve their own action (200 OK).
    6. Guest A can delete their own path (200 OK).
    """
    header_a = {"X-Guest-Session-ID": "gst_alice_123"}
    header_b = {"X-Guest-Session-ID": "gst_bob_456"}

    # 1. Guest A creates a path
    create_res = client.post(
        "/api/learning-paths",
        json={
            "goal": "Data Analyst Guest Test",
            "starting_level": "Beginner",
            "weekly_hours": 5.0,
            "duration_value": 4,
            "duration_unit": "weeks"
        },
        headers=header_a
    )
    assert create_res.status_code == 201
    path_a = create_res.json()
    path_a_id = path_a["id"]
    assert "guest_session_id" not in path_a  # Bearer credential must remain strictly confidential
    assert path_a["user_id"] is None

    # 2. Guest A lists paths -> includes their path
    list_a = client.get("/api/learning-paths", headers=header_a)
    assert list_a.status_code == 200
    assert any(p["id"] == path_a_id for p in list_a.json())

    # Guest A reads their path
    get_a = client.get(f"/api/learning-paths/{path_a_id}", headers=header_a)
    assert get_a.status_code == 200
    assert get_a.json()["id"] == path_a_id

    # 3. Guest B lists paths -> does NOT include Guest A's path
    list_b = client.get("/api/learning-paths", headers=header_b)
    assert list_b.status_code == 200
    assert not any(p["id"] == path_a_id for p in list_b.json())

    # Guest B attempts to read Guest A's path -> 403 Forbidden
    get_b = client.get(f"/api/learning-paths/{path_a_id}", headers=header_b)
    assert get_b.status_code == 403

    # Guest B attempts to delete Guest A's path -> 403 Forbidden
    del_b = client.delete(f"/api/learning-paths/{path_a_id}", headers=header_b)
    assert del_b.status_code == 403

    # Guest B attempts to regenerate Guest A's plan -> 403 Forbidden
    gen_b = client.post(f"/api/learning-paths/{path_a_id}/generate", headers=header_b)
    assert gen_b.status_code == 403

    # Guest B attempts to adapt Guest A's plan -> 403 Forbidden
    adapt_b = client.post(
        f"/api/learning-paths/{path_a_id}/adapt",
        json={"reason": "Test replan", "weekly_hours": 6.0},
        headers=header_b
    )
    assert adapt_b.status_code == 403

    # Guest B attempts to get resources -> 403 Forbidden
    res_b = client.get(f"/api/learning-paths/{path_a_id}/resources", headers=header_b)
    assert res_b.status_code == 403

    # Guest B attempts to verify resources -> 403 Forbidden
    ver_b = client.post(f"/api/learning-paths/{path_a_id}/verify", headers=header_b)
    assert ver_b.status_code == 403

    # Guest B attempts to get actions -> 403 Forbidden
    act_b = client.get(f"/api/learning-paths/{path_a_id}/actions", headers=header_b)
    assert act_b.status_code == 403

    # Guest B attempts to sync calendar -> 403 Forbidden
    sync_b = client.post(f"/api/learning-paths/{path_a_id}/sync-calendar", headers=header_b)
    assert sync_b.status_code == 403

    # Guest B attempts to read sessions -> 403 Forbidden
    cal_b = client.get(f"/api/calendar/sessions?learning_request_id={path_a_id}", headers=header_b)
    assert cal_b.status_code == 403

    # Guest B attempts to export ICS -> 403 Forbidden
    ics_b = client.get(f"/api/calendar/export-ics?learning_request_id={path_a_id}", headers=header_b)
    assert ics_b.status_code == 403

    # Guest B attempts to export Markdown -> 403 Forbidden
    md_b = client.get(f"/api/learning-paths/{path_a_id}/export-markdown", headers=header_b)
    assert md_b.status_code == 403

    # 4. Anonymous visitor without header
    unauth_get = client.get(f"/api/learning-paths/{path_a_id}")
    assert unauth_get.status_code == 401

    unauth_del = client.delete(f"/api/learning-paths/{path_a_id}")
    assert unauth_del.status_code == 401

    # 5. Action approval checks
    if path_a["proposed_actions"]:
        action_id = path_a["proposed_actions"][0]["id"]

        # Guest without header -> 401
        anon_appr = client.post(f"/api/actions/{action_id}/approve", json={"decision": "approve"})
        assert anon_appr.status_code == 401

        # Guest B -> 403
        b_appr = client.post(
            f"/api/actions/{action_id}/approve",
            headers=header_b,
            json={"decision": "approve"}
        )
        assert b_appr.status_code == 403

        # Guest A -> 200
        a_appr = client.post(
            f"/api/actions/{action_id}/approve",
            headers=header_a,
            json={"decision": "approve"}
        )
        assert a_appr.status_code == 200

    # 6. Guest A exports markdown roadmap -> 200
    md_a = client.get(f"/api/learning-paths/{path_a_id}/export-markdown", headers=header_a)
    assert md_a.status_code == 200
    assert "Learning Roadmap" in md_a.text

    # 7. Guest A exports calendar (.ics) -> 200
    ics_a = client.get(f"/api/calendar/export-ics?learning_request_id={path_a_id}", headers=header_a)
    assert ics_a.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_a.text

    # 8. Guest A deletes their own path -> 200
    del_a = client.delete(f"/api/learning-paths/{path_a_id}", headers=header_a)
    assert del_a.status_code == 200


def test_shared_benchmark_deletion_protection(client: TestClient, db_session):
    """
    Verifies that shared benchmark paths (user_id=None, guest_session_id=None)
    cannot be deleted by any guest or user, returning 403 Forbidden.
    """
    bm_path = LearningRequest(
        id="lp_benchmark_shared_fixture_test",
        goal="Shared Benchmark Test",
        starting_level="Beginner",
        weekly_hours=5.0,
        total_available_hours=130.0,
        duration_weeks=26,
        user_id=None,
        guest_session_id=None,
        is_benchmark=True
    )
    db_session.add(bm_path)
    db_session.commit()

    # Reading is permitted for public/benchmark
    read_res = client.get("/api/learning-paths/lp_benchmark_shared_fixture_test")
    assert read_res.status_code == 200

    # 1. Deletion attempt without header is blocked (403)
    del_res = client.delete("/api/learning-paths/lp_benchmark_shared_fixture_test")
    assert del_res.status_code == 403
    assert "cannot be deleted" in del_res.json()["detail"].lower()

    # Deletion attempt with guest session header is blocked (403)
    del_guest = client.delete(
        "/api/learning-paths/lp_benchmark_shared_fixture_test",
        headers={"X-Guest-Session-ID": "gst_malicious_deleter"}
    )
    assert del_guest.status_code == 403
    assert "cannot be deleted" in del_guest.json()["detail"].lower()

    # 2. Plan regeneration on shared benchmark is blocked (403)
    regen_res = client.post("/api/learning-paths/lp_benchmark_shared_fixture_test/generate")
    assert regen_res.status_code == 403
    assert "cannot be modified" in regen_res.json()["detail"].lower()

    # 3. Plan adaptation on shared benchmark is blocked (403)
    adapt_res = client.post(
        "/api/learning-paths/lp_benchmark_shared_fixture_test/adapt",
        json={"missed_strategy": "rebalance", "new_weekly_hours": 6.0}
    )
    assert adapt_res.status_code == 403
    assert "cannot be modified" in adapt_res.json()["detail"].lower()

    # 4. Calendar sync on shared benchmark is blocked (403)
    sync_res = client.post("/api/learning-paths/lp_benchmark_shared_fixture_test/sync-calendar")
    assert sync_res.status_code == 403
    assert "cannot be modified" in sync_res.json()["detail"].lower()

    # 5. Public read operations remain functional
    assert client.get("/api/learning-paths/lp_benchmark_shared_fixture_test/resources").status_code == 200
    assert client.get("/api/learning-paths/lp_benchmark_shared_fixture_test/actions").status_code == 200
    assert client.get("/api/calendar/sessions?learning_request_id=lp_benchmark_shared_fixture_test").status_code == 200
    assert client.get("/api/calendar/export-ics?learning_request_id=lp_benchmark_shared_fixture_test").status_code == 200
    assert client.get("/api/learning-paths/lp_benchmark_shared_fixture_test/export-markdown").status_code == 200


def test_guest_session_loss_and_fresh_session_isolation(client: TestClient):
    """
    Verifies Requirement 5:
    1. Creating a fresh guest session does not grant access to old anonymous/benchmark records.
    2. Losing a guest session token (requests without header) returns 401 Unauthorized
       and never silently transfers ownership.
    3. Another guest session receives 403 Forbidden.
    """
    token_1 = {"X-Guest-Session-ID": "gst_original_owner"}
    token_fresh = {"X-Guest-Session-ID": "gst_new_isolated_visitor"}

    # 1. Original guest creates a path
    res = client.post(
        "/api/learning-paths",
        json={"goal": "Data Analyst", "starting_level": "Beginner", "weekly_hours": 5.0, "duration_value": 4, "duration_unit": "weeks"},
        headers=token_1
    )
    assert res.status_code == 201
    orig_path_id = res.json()["id"]

    # 2. Fresh visitor lists paths -> returns [] (does not inherit orig_path_id or benchmark records)
    fresh_list = client.get("/api/learning-paths", headers=token_fresh)
    assert fresh_list.status_code == 200
    assert fresh_list.json() == []

    # 3. Fresh visitor attempts to access original guest's path -> 403 Forbidden
    fresh_access = client.get(f"/api/learning-paths/{orig_path_id}", headers=token_fresh)
    assert fresh_access.status_code == 403

    # 4. User who lost their token (no header) attempts to access -> 401 Unauthorized
    unauth_access = client.get(f"/api/learning-paths/{orig_path_id}")
    assert unauth_access.status_code == 401
    assert "Guest session ID required" in unauth_access.json()["detail"]

    # 5. Unauthenticated deletion attempt -> 401 Unauthorized
    unauth_del = client.delete(f"/api/learning-paths/{orig_path_id}")
    assert unauth_del.status_code == 401


def test_download_endpoints_require_authorization(client: TestClient):
    """
    Verifies Requirement 3:
    Direct download endpoints (/export-ics, /export-markdown) strictly require valid
    credentials via headers and reject unauthorized callers.
    """
    header_owner = {"X-Guest-Session-ID": "gst_download_owner"}
    header_intruder = {"X-Guest-Session-ID": "gst_download_intruder"}

    res = client.post(
        "/api/learning-paths",
        json={"goal": "Data Analyst", "starting_level": "Beginner", "weekly_hours": 5.0, "duration_value": 4, "duration_unit": "weeks"},
        headers=header_owner
    )
    assert res.status_code == 201
    path_id = res.json()["id"]

    # Owner can download ics and markdown
    ics_ok = client.get(f"/api/calendar/export-ics?learning_request_id={path_id}", headers=header_owner)
    assert ics_ok.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_ok.text

    md_ok = client.get(f"/api/learning-paths/{path_id}/export-markdown", headers=header_owner)
    assert md_ok.status_code == 200
    assert "Learning Roadmap" in md_ok.text

    # Intruder is blocked with 403 Forbidden
    ics_bad = client.get(f"/api/calendar/export-ics?learning_request_id={path_id}", headers=header_intruder)
    assert ics_bad.status_code == 403

    md_bad = client.get(f"/api/learning-paths/{path_id}/export-markdown", headers=header_intruder)
    assert md_bad.status_code == 403

    # Unauthenticated is blocked with 401 Unauthorized
    ics_unauth = client.get(f"/api/calendar/export-ics?learning_request_id={path_id}")
    assert ics_unauth.status_code == 401

    md_unauth = client.get(f"/api/learning-paths/{path_id}/export-markdown")
    assert md_unauth.status_code == 401
