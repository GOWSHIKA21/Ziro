"""
Actions REST API Router
Handles explicit human approvals, rejections, edits, and idempotent execution
for proposed course enrollments and study calendar blocks.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProposedAction, User
from ..schemas import ProposedActionSchema, ActionDecisionRequest, ActionEditRequest
from ..services.action_service import action_service
from ..services.auth_service import (
    get_current_user_optional,
    get_guest_session_id_optional,
    verify_learning_path_access
)

router = APIRouter(prefix="/api/actions", tags=["Actions & Human Approval"])

@router.post("/{id}/approve", response_model=ProposedActionSchema)
def approve_action(
    id: str,
    payload: ActionDecisionRequest = ActionDecisionRequest(decision="approve"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Explicitly approve a proposed course enrollment or study calendar block.
    Upon approval, triggers idempotent execution and verification.
    """
    action = db.query(ProposedAction).filter(ProposedAction.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{id}' not found.")

    if action.learning_request:
        verify_learning_path_access(action.learning_request, current_user, guest_session_id, is_mutation=True)

    updated_action = action_service.approve_action(db, action, notes=payload.notes)
    return updated_action


@router.post("/{id}/reject", response_model=ProposedActionSchema)
def reject_action(
    id: str,
    payload: ActionDecisionRequest = ActionDecisionRequest(decision="reject"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Explicitly reject a proposed action. Marks action as Rejected and prevents execution.
    """
    action = db.query(ProposedAction).filter(ProposedAction.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{id}' not found.")

    if action.learning_request:
        verify_learning_path_access(action.learning_request, current_user, guest_session_id, is_mutation=True)

    updated_action = action_service.reject_action(db, action, notes=payload.notes)
    return updated_action


@router.post("/{id}/edit", response_model=ProposedActionSchema)
def edit_action(
    id: str,
    payload: ActionEditRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Edit action details (e.g. customize scheduled study times) before approval.
    """
    action = db.query(ProposedAction).filter(ProposedAction.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{id}' not found.")

    if action.learning_request:
        verify_learning_path_access(action.learning_request, current_user, guest_session_id, is_mutation=True)

    if action.approval_status != "Pending Approval":
        raise HTTPException(status_code=400, detail="Cannot edit an action that has already been approved or rejected.")

    if payload.title:
        action.title = payload.title
    if payload.schedule_details:
        current_details = dict(action.schedule_details or {})
        current_details.update(payload.schedule_details)
        action.schedule_details = current_details

    db.commit()
    db.refresh(action)
    return action


@router.post("/{id}/execute", response_model=ProposedActionSchema)
def execute_action_manually(
    id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Manually trigger execution of an already approved action.
    Maintains idempotency: safe to call repeatedly.
    """
    action = db.query(ProposedAction).filter(ProposedAction.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{id}' not found.")

    if action.learning_request:
        verify_learning_path_access(action.learning_request, current_user, guest_session_id, is_mutation=True)

    if action.approval_status != "Approved":
        raise HTTPException(status_code=400, detail="Action must be Approved before execution.")

    updated_action = action_service.execute_action(db, action)
    return updated_action
