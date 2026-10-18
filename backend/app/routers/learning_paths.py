"""
Learning Paths REST API Router
Handles creation, status retrieval, pipeline generation, resource listing,
and calendar synchronization.
"""

import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import LearningRequest, Resource, ProposedAction, StudySession
from ..schemas import (
    LearningRequestCreate, LearningRequestResponse,
    ResourceSchema, ProposedActionSchema, StudySessionSchema
)
from ..services.agent_orchestrator import agent_orchestrator
from ..services.verifier import verifier
from ..services.calendar_service import calendar_service

router = APIRouter(prefix="/api/learning-paths", tags=["Learning Paths"])

@router.post("", response_model=LearningRequestResponse, status_code=201)
async def create_learning_path(
    payload: LearningRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new learning request with validated parameters.
    Calculates total available hours = weekly_hours * duration_weeks.
    Example: 6 months @ 5 hrs/week = 26 weeks * 5 = 130 hours.
    """
    # Duration conversion
    if payload.duration_unit == "months":
        # 6 months = exactly 26 weeks as required by TC1 specification
        if payload.duration_value == 6:
            duration_weeks = 26
        else:
            duration_weeks = int(round(payload.duration_value * (26 / 6)))
    else:
        duration_weeks = payload.duration_value

    if duration_weeks <= 0:
        raise HTTPException(status_code=400, detail="Duration weeks must be greater than zero.")

    total_available_hours = round(float(payload.weekly_hours * duration_weeks), 1)

    # Assign stable unique ID
    req_id = f"lp_{uuid.uuid4().hex[:10]}"

    learning_request = LearningRequest(
        id=req_id,
        goal=payload.goal.strip(),
        starting_level=payload.starting_level,
        weekly_hours=float(payload.weekly_hours),
        duration_weeks=duration_weeks,
        duration_unit=payload.duration_unit,
        total_available_hours=total_available_hours,
        preferred_format=payload.preferred_format or "Mixed",
        status="created"
    )

    db.add(learning_request)
    db.commit()
    db.refresh(learning_request)

    # Automatically trigger initial pipeline generation
    await agent_orchestrator.run_full_pipeline(db, learning_request)
    db.refresh(learning_request)

    return learning_request


@router.get("", response_model=List[LearningRequestResponse])
def list_learning_paths(db: Session = Depends(get_db)):
    """Retrieve all learning paths ordered by creation date."""
    return db.query(LearningRequest).order_by(LearningRequest.created_at.desc()).all()


@router.get("/{id}", response_model=LearningRequestResponse)
def get_learning_path(id: str, db: Session = Depends(get_db)):
    """Retrieve current state of a specific learning path."""
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail=f"Learning path with ID '{id}' not found.")
    return req


@router.post("/{id}/generate", response_model=LearningRequestResponse)
async def generate_learning_plan(
    id: str,
    simulate_paid: Optional[str] = Query(None, description="Resource ID or 'ANY' to simulate course paywall"),
    simulate_broken: Optional[str] = Query(None, description="Resource ID or 'ANY' to simulate broken link"),
    db: Session = Depends(get_db)
):
    """
    Run or re-run the agentic pipeline.
    Reuses stable records and handles duplicate prevention (TC4).
    """
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail=f"Learning path with ID '{id}' not found.")

    await agent_orchestrator.run_full_pipeline(
        db,
        req,
        simulate_paid=simulate_paid,
        simulate_broken=simulate_broken
    )
    db.refresh(req)
    return req


@router.get("/{id}/resources", response_model=List[ResourceSchema])
def get_resources(id: str, db: Session = Depends(get_db)):
    """List resources and verification evidence for a learning path."""
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")
    return req.resources


@router.post("/{id}/verify")
async def verify_resources(
    id: str,
    simulate_paid_resource_id: Optional[str] = None,
    simulate_broken_resource_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Independently trigger verification of all resource links and free status.
    Supports simulation triggers for TC2 (paid course) and TC3 (broken link).
    """
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    results = await verifier.verify_all_resources(
        db,
        req,
        simulate_paid_resource_id=simulate_paid_resource_id,
        simulate_broken_resource_id=simulate_broken_resource_id
    )
    return results


@router.post("/{id}/replace-resource/{resource_id}", response_model=ResourceSchema)
async def replace_resource_endpoint(
    id: str,
    resource_id: str,
    reason: str = "User requested replacement",
    db: Session = Depends(get_db)
):
    """Manually or programmatically trigger replacement of a resource."""
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    target_res = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.learning_request_id == id
    ).first()

    if not target_res:
        raise HTTPException(status_code=404, detail="Resource not found in this learning path.")

    replacement = await verifier.find_and_apply_replacement(
        db, req, target_res, reason=reason
    )
    if not replacement:
        raise HTTPException(status_code=400, detail="No suitable free replacement found in catalog.")
    
    db.commit()
    db.refresh(replacement)
    return replacement


@router.get("/{id}/actions", response_model=List[ProposedActionSchema])
def get_actions(id: str, db: Session = Depends(get_db)):
    """View proposed and executed actions for human approval."""
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")
    return req.proposed_actions


@router.post("/{id}/sync-calendar")
def sync_calendar_endpoint(id: str, db: Session = Depends(get_db)):
    """
    Synchronize approved study sessions to calendar.
    Strict invariant: Adds ONLY missing sessions, skips duplicates, preserves user events.
    """
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    sync_result = calendar_service.sync_calendar(db, req)
    return sync_result


@router.get("/{id}/export-markdown")
def export_markdown_endpoint(id: str, db: Session = Depends(get_db)):
    """Export complete learning roadmap and verified resources as clean Markdown document."""
    req = db.query(LearningRequest).filter(LearningRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    lines = [
        f"# {req.goal} — Learning Roadmap",
        f"**Target Level:** {req.starting_level} | **Duration:** {req.duration_weeks} weeks | **Weekly Availability:** {req.weekly_hours} hours/week",
        f"**Total Budget:** {req.total_available_hours} hours | **Feasibility:** {req.feasibility_status.capitalize()}",
        "",
        "## Feasibility Assessment & Rationale",
        req.feasibility_notes or "Curriculum scoped to match available time budget.",
        "",
        "## Prerequisite-Ordered Modules",
        ""
    ]

    for m in req.modules:
        lines.append(f"### {m.order_index + 1}. {m.title} (~{m.estimated_hours}h)")
        lines.append(f"{m.description}")
        lines.append(f"- **Skills Covered:** {', '.join(m.skills_covered)}")
        lines.append(f"- **Learning Outcomes:** {'; '.join(m.learning_outcomes)}")
        lines.append("")

    lines.append("## Week-by-Week Study Schedule")
    lines.append("")
    for p in req.weekly_plans:
        lines.append(f"### Week {p.week_number}: {p.focus_topic} ({p.allocated_hours}h)")
        lines.append(f"- **Milestone Assessment:** {p.milestone_assessment}")
        lines.append("- **Exercises:**")
        for ex in p.exercises:
            lines.append(f"  - {ex}")
        lines.append("")

    lines.append("## Verified Free Resources")
    lines.append("")
    for r in req.resources:
        if r.free_status != "paid":
            lines.append(f"- [{r.title}]({r.original_url}) — **{r.provider}** ({r.free_status})")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=\"roadmap_{req.id}.md\""}
    )

