"""
Agent Orchestrator
Coordinates the complete multi-stage agentic workflow:
Stage A (Goal Analysis) -> Stage B (Resource Discovery) -> Stage C (Planning)
-> Stage D (Verification) -> Stage E (Action Proposal) -> Stage F (Execution)
Ensures full audit logs, persistent state transitions, and idempotent reruns (TC4).
"""

import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import LearningRequest, AgentLog, utc_now
from .goal_analyzer import goal_analyzer
from .resource_discovery import resource_discovery
from .planner import planner
from .verifier import verifier
from .action_service import action_service

class AgentOrchestrator:
    async def run_full_pipeline(
        self,
        db: Session,
        learning_request: LearningRequest,
        simulate_paid: Optional[str] = None,
        simulate_broken: Optional[str] = None
    ) -> LearningRequest:
        """
        Executes the end-to-end agentic workflow across Stages A through E.
        """
        # Starting orchestrator run
        start_log = AgentLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            learning_request_id=learning_request.id,
            stage="Workflow Pipeline",
            status="started",
            message=f"Starting end-to-end agent workflow for '{learning_request.goal}' ({learning_request.starting_level}, {learning_request.weekly_hours}h/wk, {learning_request.duration_weeks} wks).",
            details={"start_time": utc_now().isoformat()}
        )
        db.add(start_log)
        db.commit()

        # Stage A: Goal Analysis
        learning_request.status = "analyzing"
        db.commit()
        modules, curriculum = goal_analyzer.analyze_and_create_modules(db, learning_request)

        # Stage B: Resource Discovery
        learning_request.status = "discovering"
        db.commit()
        resources = resource_discovery.discover_resources_for_modules(db, learning_request, modules)

        # Stage C: Prerequisite-Aware Planning
        learning_request.status = "planning"
        db.commit()
        weekly_plans = planner.create_weekly_plan(db, learning_request, modules, curriculum)

        # Stage D: Resource Verification
        learning_request.status = "verifying"
        db.commit()
        verification_results = await verifier.verify_all_resources(
            db,
            learning_request,
            simulate_paid_resource_id=simulate_paid,
            simulate_broken_resource_id=simulate_broken
        )

        # Stage E: Action Proposal & Human Approval Preparation
        learning_request.status = "actions_proposed"
        db.commit()
        proposed_actions = action_service.generate_proposed_actions(db, learning_request)

        # Final state for user interaction
        learning_request.status = "ready_for_approval"
        learning_request.updated_at = utc_now()
        db.commit()

        # Pipeline complete log
        complete_log = AgentLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            learning_request_id=learning_request.id,
            stage="Workflow Pipeline",
            status="completed",
            message=f"Agent workflow complete. {len(modules)} modules, {len(weekly_plans)} weeks planned, {len(resources)} resources verified, {len(proposed_actions)} actions proposed for approval.",
            details={
                "modules_count": len(modules),
                "weeks_count": len(weekly_plans),
                "resources_count": len(resources),
                "proposed_actions_count": len(proposed_actions),
                "verification_summary": verification_results
            }
        )
        db.add(complete_log)
        db.commit()
        db.refresh(learning_request)

        return learning_request

agent_orchestrator = AgentOrchestrator()
