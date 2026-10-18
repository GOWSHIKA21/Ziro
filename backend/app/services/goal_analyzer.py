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

        raw_modules_data = curriculum.get("modules", [])
        modules_data = self.detect_cycles_and_toposort(raw_modules_data)
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

    @staticmethod
    def detect_cycles_and_toposort(modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates prerequisite relationships, detects cycles in the dependency graph,
        and returns a topologically sorted list of modules ensuring foundational
        milestones precede dependent specializations.
        """
        if not modules_data:
            return []

        title_to_index = {m.get("title", "").lower(): i for i, m in enumerate(modules_data)}
        adj: Dict[int, List[int]] = {i: [] for i in range(len(modules_data))}
        in_degree = {i: 0 for i in range(len(modules_data))}

        for i, mod in enumerate(modules_data):
            for prereq in mod.get("prerequisites", []):
                prereq_lower = str(prereq).lower()
                for t, idx in title_to_index.items():
                    if prereq_lower in t or t in prereq_lower:
                        if idx != i:
                            adj[idx].append(i)
                            in_degree[i] += 1
                        break

        queue = [i for i in range(len(modules_data)) if in_degree[i] == 0]
        sorted_indices: List[int] = []

        while queue:
            curr = queue.pop(0)
            sorted_indices.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If a cycle was detected (not all nodes processed), append remaining nodes safely
        if len(sorted_indices) < len(modules_data):
            for i in range(len(modules_data)):
                if i not in sorted_indices:
                    sorted_indices.append(i)

        return [modules_data[i] for i in sorted_indices]

goal_analyzer = GoalAnalyzer()
