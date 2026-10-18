"""
TC2 — Course Has Become Paid
Simulate a previously free course becoming paid.
Expected: The agent flags the course, records the evidence, finds a suitable free replacement
when possible, verifies the replacement, and updates the roadmap.
If no replacement can be verified, clearly flag the unresolved resource.
"""

import pytest

def test_tc2_course_becomes_paid(client):
    # 1. Create initial learning path
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 8,
        "duration_unit": "weeks"
    }

    create_res = client.post("/api/learning-paths", json=payload)
    assert create_res.status_code == 201
    path_data = create_res.json()
    path_id = path_data["id"]

    assert len(path_data["resources"]) > 0
    target_resource = path_data["resources"][0]
    initial_res_count = len(path_data["resources"])

    # 2. Simulate course becoming paid via verify endpoint with simulate_paid_resource_id
    verify_res = client.post(
        f"/api/learning-paths/{path_id}/verify",
        params={"simulate_paid_resource_id": target_resource["id"]}
    )
    assert verify_res.status_code == 200
    summary = verify_res.json()

    assert summary["flagged_paid_count"] >= 1
    assert summary["replaced_count"] >= 1

    # 3. Fetch updated learning path
    updated_res = client.get(f"/api/learning-paths/{path_id}")
    assert updated_res.status_code == 200
    updated_data = updated_res.json()

    # Verify flagged resource
    flagged_res = next(r for r in updated_data["resources"] if r["id"] == target_resource["id"])
    assert flagged_res["free_status"] == "paid"
    assert flagged_res["verification_status"] == "flagged"
    assert "paywall" in flagged_res["verification_notes"].lower() or "paid" in flagged_res["verification_notes"].lower()

    # Verify replacement resource
    replacements = [r for r in updated_data["resources"] if r["is_replacement"]]
    assert len(replacements) >= 1
    rep = replacements[0]
    assert rep["replaces_resource_id"] == target_resource["id"]
    assert rep["free_status"] == "verified_free"
    assert rep["verification_status"] == "verified"
    assert rep["provider"] != ""
    assert rep["original_url"].startswith("http")

    # 4. Verify official test runner TC2 passes
    test_res = client.post("/api/test-runs", json={"scenario_id": "TC2"})
    assert test_res.status_code == 200
    runs = test_res.json()
    assert runs[0]["scenario_id"] == "TC2"
    assert runs[0]["status"] == "passed"
    assert runs[0]["verification_evidence"]["replacement_found"] is True
