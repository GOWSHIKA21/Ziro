"""
API and Validation Tests
Covers input validation, action approval lifecycle, user-created calendar preservation,
and feasibility assessments.
"""

import pytest

def test_input_validation_empty_goal(client):
    payload = {
        "goal": "   ",  # Blank
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    res = client.post("/api/learning-paths", json=payload)
    assert res.status_code == 422, "Empty goal must return 422 Unprocessable Entity"


def test_input_validation_nonpositive_hours(client):
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 0.0,  # Invalid
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    res = client.post("/api/learning-paths", json=payload)
    assert res.status_code == 422, "Non-positive hours must be rejected"

    payload["weekly_hours"] = -5.0
    res = client.post("/api/learning-paths", json=payload)
    assert res.status_code == 422


def test_input_validation_unreasonable_weekly_hours(client):
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 120.0,  # Unreasonable (> 80 hrs/wk)
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    res = client.post("/api/learning-paths", json=payload)
    assert res.status_code == 422, "Unreasonable weekly hours must be rejected"


def test_action_approval_and_rejection_lifecycle(client):
    # Create path
    payload = {
        "goal": "Web Developer",
        "starting_level": "Beginner",
        "weekly_hours": 10.0,
        "duration_value": 8,
        "duration_unit": "weeks"
    }
    res = client.post("/api/learning-paths", json=payload)
    assert res.status_code == 201
    path_data = res.json()
    path_id = path_data["id"]

    actions = path_data["proposed_actions"]
    assert len(actions) >= 2

    # 1. Test Approval
    action_to_approve = actions[0]
    appr_res = client.post(
        f"/api/actions/{action_to_approve['id']}/approve",
        json={"decision": "approve", "notes": "Approved for learning"}
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["approval_status"] == "Approved"
    assert appr_data["execution_status"] in ["Executed", "Verified"]
    assert appr_data["decision_notes"] == "Approved for learning"

    # 2. Test Rejection
    action_to_reject = actions[1]
    rej_res = client.post(
        f"/api/actions/{action_to_reject['id']}/reject",
        json={"decision": "reject", "notes": "Not interested in this course"}
    )
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    assert rej_data["approval_status"] == "Rejected"
    assert rej_data["execution_status"] == "Failed"


def test_calendar_preserves_user_created_events(client):
    # Create path
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    res = client.post("/api/learning-paths", json=payload)
    path_data = res.json()
    path_id = path_data["id"]

    # Create a user-created study session
    user_session_payload = {
        "learning_request_id": path_id,
        "title": "My Custom Group Study Session",
        "scheduled_date": "2026-11-01",
        "start_time": "14:00",
        "end_time": "16:00",
        "duration_hours": 2.0
    }
    create_user_sess = client.post("/api/calendar/sessions", json=user_session_payload)
    assert create_user_sess.status_code == 201
    user_sess = create_user_sess.json()
    assert user_sess["is_user_created"] is True

    # Approve all calendar actions and sync
    cal_action = next(a for a in path_data["proposed_actions"] if a["action_type"] == "calendar_block")
    client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})

    # Sync calendar
    sync_res = client.post(f"/api/learning-paths/{path_id}/sync-calendar")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()

    # Verify user session is strictly preserved
    assert sync_data["preserved_user_events"] >= 1
    session_titles = [s["title"] for s in sync_data["sessions"]]
    assert "My Custom Group Study Session" in session_titles
