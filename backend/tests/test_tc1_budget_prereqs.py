"""
TC1 — Six Months at Five Hours per Week
Input: Goal = Data Analyst; Starting Level = Beginner; Weekly Availability = 5 hours; Duration = 26 weeks.
Expected: The generated learning plan fits within approximately 130 total available hours,
respects the weekly budget, and orders prerequisite skills correctly.
"""

import pytest

def test_tc1_six_months_at_five_hours(client):
    payload = {
        "goal": "Data Analyst",
        "starting_level": "Beginner",
        "weekly_hours": 5.0,
        "duration_value": 6,
        "duration_unit": "months",
        "preferred_format": "Mixed"
    }

    response = client.post("/api/learning-paths", json=payload)
    assert response.status_code == 201
    data = response.json()

    # 1. Total available hours calculation: 6 months = 26 weeks * 5 = 130 hours
    assert data["duration_weeks"] == 26
    assert data["weekly_hours"] == 5.0
    assert data["total_available_hours"] == 130.0

    # 2. Check weekly plans count and allocation
    weekly_plans = data["weekly_plans"]
    assert len(weekly_plans) == 26, f"Expected 26 weekly plans, got {len(weekly_plans)}"

    total_allocated = sum(p["allocated_hours"] for p in weekly_plans)
    assert total_allocated <= 130.0, f"Total allocated {total_allocated} exceeds budget 130.0"

    # 3. Check every single week respects weekly availability budget (<= 5.0)
    for p in weekly_plans:
        assert p["allocated_hours"] <= 5.0, (
            f"Week {p['week_number']} allocated {p['allocated_hours']} hrs which exceeds 5.0h budget!"
        )
        assert len(p["exercises"]) > 0, f"Week {p['week_number']} missing exercises"
        assert p["milestone_assessment"] is not None, f"Week {p['week_number']} missing milestone"

    # 4. Prerequisite Skill Ordering
    modules = data["modules"]
    assert len(modules) >= 3, "Expected at least 3 learning modules"

    # Ensure order_index is ascending
    indices = [m["order_index"] for m in modules]
    assert indices == sorted(indices), "Module order_index is not strictly sorted"

    # Find foundational spreadsheet module and verify it precedes advanced capstone
    titles_lower = [m["title"].lower() for m in modules]
    foundations_idx = next(i for i, t in enumerate(titles_lower) if "spreadsheet" in t or "excel" in t)
    sql_idx = next(i for i, t in enumerate(titles_lower) if "sql" in t or "database" in t)
    capstone_idx = next(i for i, t in enumerate(titles_lower) if "capstone" in t or "portfolio" in t)

    assert foundations_idx < sql_idx, "Foundational spreadsheets must precede SQL"
    assert sql_idx < capstone_idx, "SQL must precede capstone portfolio"

    # 5. Verify official test runner executes TC1 and marks passed
    test_res = client.post("/api/test-runs", json={"scenario_id": "TC1"})
    assert test_res.status_code == 200
    runs = test_res.json()
    assert len(runs) == 1
    assert runs[0]["scenario_id"] == "TC1"
    assert runs[0]["status"] == "passed"
    assert runs[0]["verification_evidence"]["assert_weekly_budget_passed"] is True
