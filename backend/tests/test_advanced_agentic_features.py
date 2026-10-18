"""
Tests for Advanced Agentic Capabilities & Innovation:
- Action editing prior to approval (human-in-the-loop parameter customization)
- Universal RFC 5545 iCalendar (.ics) export
- Interactive study session completion toggle
- Roadmap Markdown export
"""

import pytest

def test_edit_action_parameters(client):
    # 1. Create a learning path
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    create_res = client.post("/api/learning-paths", json=payload)
    assert create_res.status_code == 201
    path_data = create_res.json()

    cal_action = next(a for a in path_data["proposed_actions"] if a["action_type"] == "calendar_block")
    assert cal_action["approval_status"] == "Pending Approval"

    # 2. Human operator edits the proposed action parameters
    edit_payload = {
        "title": "Custom Study Slot: Weekend Deep Dive (5.0h)",
        "schedule_details": {
            "suggested_time": "10:00 - 15:00",
            "duration_per_session_hours": 5.0
        }
    }
    edit_res = client.post(f"/api/actions/{cal_action['id']}/edit", json=edit_payload)
    assert edit_res.status_code == 200
    edited = edit_res.json()

    assert edited["title"] == "Custom Study Slot: Weekend Deep Dive (5.0h)"
    assert edited["schedule_details"]["suggested_time"] == "10:00 - 15:00"
    assert edited["schedule_details"]["duration_per_session_hours"] == 5.0

    # 3. Approve edited action
    appr_res = client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "Approved"


def test_calendar_export_ics(client):
    # 1. Create path and approve calendar block
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    create_res = client.post("/api/learning-paths", json=payload)
    path_data = create_res.json()
    path_id = path_data["id"]

    cal_action = next(a for a in path_data["proposed_actions"] if a["action_type"] == "calendar_block")
    client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})

    # 2. Export RFC 5545 iCalendar stream
    ics_res = client.get(f"/api/calendar/export-ics?learning_request_id={path_id}")
    assert ics_res.status_code == 200
    assert "text/calendar" in ics_res.headers["content-type"]
    ics_text = ics_res.text

    assert "BEGIN:VCALENDAR" in ics_text
    assert "VERSION:2.0" in ics_text
    assert "BEGIN:VEVENT" in ics_text
    assert "SUMMARY:" in ics_text
    assert "DTSTART:" in ics_text
    assert "DTEND:" in ics_text
    assert "END:VCALENDAR" in ics_text


def test_toggle_session_completion(client):
    # Create path & approve session
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    create_res = client.post("/api/learning-paths", json=payload)
    path_data = create_res.json()
    path_id = path_data["id"]

    cal_action = next(a for a in path_data["proposed_actions"] if a["action_type"] == "calendar_block")
    client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})

    # Fetch created sessions
    sess_res = client.get(f"/api/calendar/sessions?learning_request_id={path_id}")
    sessions = sess_res.json()
    assert len(sessions) > 0
    target_sess = sessions[0]
    assert target_sess["status"] == "synced_calendar"

    # Toggle to completed
    toggle_res1 = client.post(f"/api/calendar/sessions/{target_sess['id']}/toggle-complete")
    assert toggle_res1.status_code == 200
    assert toggle_res1.json()["status"] == "completed"

    # Toggle back to synced_calendar
    toggle_res2 = client.post(f"/api/calendar/sessions/{target_sess['id']}/toggle-complete")
    assert toggle_res2.status_code == 200
    assert toggle_res2.json()["status"] == "synced_calendar"


def test_roadmap_markdown_export(client):
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }
    create_res = client.post("/api/learning-paths", json=payload)
    path_id = create_res.json()["id"]

    md_res = client.get(f"/api/learning-paths/{path_id}/export-markdown")
    assert md_res.status_code == 200
    md_text = md_res.text

    assert "# Data Analyst — Learning Roadmap" in md_text
    assert "## Prerequisite-Ordered Modules" in md_text
    assert "## Week-by-Week Study Schedule" in md_text
    assert "## Verified Free Resources" in md_text
