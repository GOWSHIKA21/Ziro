"""
Stage A: Goal Analysis
Identifies skills required for the target goal, breaks them into prerequisite-aware
learning modules, and defines measurable learning outcomes.
"""

import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import LearningRequest, LearningModule, AgentLog
from .llm_service import llm_service

class GoalAnalyzer:
    def analyze_and_create_modules(
        self,
        db: Session,
        learning_request: LearningRequest
    ) -> Tuple[List[LearningModule], Dict[str, Any]]:
        """
        Executes Stage A: Goal Analysis.
        Returns the created LearningModule records and curriculum structure.
        """
        # Call LLM or deterministic fallback
        curriculum = llm_service.analyze_goal_and_plan(
            goal=learning_request.goal,
            starting_level=learning_request.starting_level,
            weekly_hours=learning_request.weekly_hours,
            duration_weeks=learning_request.duration_weeks,
            preferred_format=learning_request.preferred_format
        )

        feasibility = curriculum.get("feasibility", {})
        learning_request.feasibility_status = feasibility.get("status", "feasible")
        learning_request.feasibility_notes = feasibility.get("notes", "")

        modules_data = curriculum.get("modules", [])
        created_modules: List[LearningModule] = []

        # Remove any pre-existing modules for idempotency
        for mod in learning_request.modules:
            db.delete(mod)
        db.flush()

        for idx, mod_info in enumerate(modules_data):
            mod_id = f"mod_{learning_request.id}_{idx+1}"
            module = LearningModule(
                id=mod_id,
                learning_request_id=learning_request.id,
                title=mod_info["title"],
                description=mod_info.get("description", ""),
                order_index=idx,
                prerequisites=mod_info.get("prerequisites", []),
                skills_covered=mod_info.get("skills_covered", []),
                learning_outcomes=mod_info.get("learning_outcomes", []),
                estimated_hours=float(mod_info.get("estimated_hours", 20.0)),
                status="pending"
            )
            db.add(module)
            created_modules.append(module)

        db.flush()

        # Log agent activity for Stage A
        log = AgentLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            learning_request_id=learning_request.id,
            stage="Stage A: Goal Analysis",
            status="completed",
            message=f"Goal analyzed into {len(created_modules)} prerequisite-ordered learning modules. Feasibility: {learning_request.feasibility_status}.",
            details={
                "goal": learning_request.goal,
                "modules_count": len(created_modules),
                "feasibility_status": learning_request.feasibility_status,
                "modules": [m.title for m in created_modules]
            }
        )
        db.add(log)
        db.commit()

        return created_modules, curriculum

goal_analyzer = GoalAnalyzer()
