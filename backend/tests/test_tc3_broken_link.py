"""
TC3 — Broken Link
Simulate a resource URL returning a broken-link response.
Expected: The agent records the failure, searches for a replacement covering similar skills,
checks the replacement URL and free-access evidence, and updates the learning plan only when the replacement is suitable.
If replacement verification fails, keep the issue visible.
"""

import pytest

def test_tc3_broken_link_handling(client):
    # 1. Create learning path
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 6,
        "duration_unit": "weeks"
    }

    create_res = client.post("/api/learning-paths", json=payload)
    assert create_res.status_code == 201
    path_data = create_res.json()
    path_id = path_data["id"]

    target_res = path_data["resources"][0]

    # 2. Simulate broken link (HTTP 404)
    verify_res = client.post(
        f"/api/learning-paths/{path_id}/verify",
        params={"simulate_broken_resource_id": target_res["id"]}
    )
    assert verify_res.status_code == 200
    summary = verify_res.json()

    assert summary["broken_count"] >= 1
    assert summary["replaced_count"] >= 1

    # 3. Check updated learning path
    updated_res = client.get(f"/api/learning-paths/{path_id}")
    assert updated_res.status_code == 200
    updated_data = updated_res.json()

    # Broken resource record
    broken_res = next(r for r in updated_data["resources"] if r["id"] == target_res["id"])
    assert broken_res["free_status"] == "broken"
    assert broken_res["verification_status"] == "failed"
    assert "404" in broken_res["verification_notes"] or "broken" in broken_res["verification_notes"].lower()

    # Evidence history for broken resource
    assert len(broken_res["evidence_history"]) >= 1
    evidence_item = broken_res["evidence_history"][0]
    assert evidence_item["result_status"] == "broken_link"
    assert evidence_item["http_status"] == 404

    # Replacement resource verified
    replacements = [r for r in updated_data["resources"] if r["is_replacement"]]
    assert len(replacements) >= 1
    rep = replacements[0]
    assert rep["replaces_resource_id"] == target_res["id"]
    assert rep["free_status"] == "verified_free"
    assert rep["verification_status"] == "verified"

    # 4. Verify official test runner TC3 passes
    test_res = client.post("/api/test-runs", json={"scenario_id": "TC3"})
    assert test_res.status_code == 200
    runs = test_res.json()
    assert runs[0]["scenario_id"] == "TC3"
    assert runs[0]["status"] == "passed"
    assert runs[0]["verification_evidence"]["replacement_found"] is True
