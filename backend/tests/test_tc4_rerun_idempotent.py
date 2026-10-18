"""
TC4 — Rerun Without Duplicates
Run the same learning-path request twice.
Expected: The second run reuses existing stable records and creates only genuinely missing
sessions or actions. It must not duplicate completed calendar blocks, approved actions,
or resource records unnecessarily.
Test this by comparing session IDs and calendar event counts before and after the rerun.
"""

import pytest

def test_tc4_rerun_without_duplicates(client):
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 4,
        "duration_unit": "weeks"
    }

    # 1. First run: create path
    create_res = client.post("/api/learning-paths", json=payload)
    assert create_res.status_code == 201
    path_data = create_res.json()
    path_id = path_data["id"]

    # 2. Approve a calendar block action to generate calendar study sessions
    cal_action = next(a for a in path_data["proposed_actions"] if a["action_type"] == "calendar_block")
    appr_res = client.post(f"/api/actions/{cal_action['id']}/approve", json={"decision": "approve"})
    assert appr_res.status_code == 200

    # 3. Snapshot state before rerun
    state_before_res = client.get(f"/api/learning-paths/{path_id}")
    assert state_before_res.status_code == 200
    state_before = state_before_res.json()

    actions_count_before = len(state_before["proposed_actions"])
    sessions_count_before = len(state_before["study_sessions"])
    session_ids_before = {s["id"] for s in state_before["study_sessions"]}
    assert sessions_count_before > 0, "Approved calendar block should have produced study sessions"

    # 4. Second run: trigger generation / rerun on the exact same learning path
    rerun_res = client.post(f"/api/learning-paths/{path_id}/generate")
    assert rerun_res.status_code == 200

    # Also trigger calendar sync
    sync_res = client.post(f"/api/learning-paths/{path_id}/sync-calendar")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["added_missing_sessions"] == 0, "No new sessions should be added for already synced blocks"
    assert sync_data["skipped_duplicates"] >= 1, "Duplicate sessions should be actively detected and skipped"

    # 5. Snapshot state after rerun
    state_after_res = client.get(f"/api/learning-paths/{path_id}")
    assert state_after_res.status_code == 200
    state_after = state_after_res.json()

    actions_count_after = len(state_after["proposed_actions"])
    sessions_count_after = len(state_after["study_sessions"])
    session_ids_after = {s["id"] for s in state_after["study_sessions"]}

    # 6. Verify zero duplicates
    assert actions_count_after == actions_count_before, (
        f"Actions count changed from {actions_count_before} to {actions_count_after} (duplicate action created!)"
    )
    assert sessions_count_after == sessions_count_before, (
        f"Sessions count changed from {sessions_count_before} to {sessions_count_after} (duplicate session created!)"
    )
    assert session_ids_before == session_ids_after, "Session IDs were not preserved across reruns"

    # 7. Verify official test runner TC4 passes
    test_res = client.post("/api/test-runs", json={"scenario_id": "TC4"})
    assert test_res.status_code == 200
    runs = test_res.json()
    assert runs[0]["scenario_id"] == "TC4"
    assert runs[0]["status"] == "passed"
    assert runs[0]["verification_evidence"]["duplicate_sessions_created"] == 0
