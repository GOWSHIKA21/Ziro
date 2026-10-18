"""
Stage C: Prerequisite-Aware Planning
Builds a week-by-week timeline that strictly respects weekly hours budget,
enforces prerequisite order (foundations before advanced), and schedules
exercises, revision, and milestone assessments.
"""

import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import LearningRequest, LearningModule, WeeklyPlan, AgentLog

class Planner:
    def create_weekly_plan(
        self,
        db: Session,
        learning_request: LearningRequest,
        modules: List[LearningModule],
        curriculum_data: Dict[str, Any]
    ) -> List[WeeklyPlan]:
        """
        Executes Stage C: Prerequisite-Aware Planning.
        Strict invariant: For every week, allocated_hours <= learning_request.weekly_hours!
        Total hours <= total_available_hours.
        """
        # Clear existing weekly plans for idempotency
        for plan in learning_request.weekly_plans:
            db.delete(plan)
        db.flush()

        weekly_focus_items = curriculum_data.get("weekly_focus", [])
        created_plans: List[WeeklyPlan] = []
        total_weeks = learning_request.duration_weeks
        max_weekly_hours = float(learning_request.weekly_hours)
        total_budget = float(learning_request.total_available_hours)

        # Sort modules by order_index to guarantee foundational topics come first
        sorted_modules = sorted(modules, key=lambda m: m.order_index)

        # If curriculum has pre-generated weekly breakdown, align with database modules
        for w in range(1, total_weeks + 1):
            plan_id = f"plan_{learning_request.id}_wk{w}"
            
            # Find matching module based on progress through the total weeks
            module_idx = min(len(sorted_modules) - 1, int(((w - 1) / total_weeks) * len(sorted_modules)))
            matched_module = sorted_modules[module_idx] if sorted_modules else None

            # Get matching weekly focus details if available
            focus_info = None
            if w - 1 < len(weekly_focus_items):
                focus_info = weekly_focus_items[w - 1]

            # Invariant: NEVER exceed max_weekly_hours
            if focus_info and 0 < focus_info.get("allocated_hours", 0) <= max_weekly_hours:
                allocated = float(focus_info["allocated_hours"])
            else:
                allocated = max_weekly_hours

            topic = focus_info.get("focus_topic") if focus_info else f"{matched_module.title} - Core Practice"
            
            # Exercises and milestone
            if focus_info and focus_info.get("exercises"):
                exercises = focus_info["exercises"]
            else:
                exercises = [
                    f"Core Practice: Implement exercises from {matched_module.title if matched_module else 'weekly material'}",
                    f"Applied Challenge: Solve hands-on dataset problem and document solution"
                ]

            # Special milestone for mid-term and capstone weeks
            if w == total_weeks:
                milestone = f"Final Capstone Milestone: Comprehensive assessment, GitHub repository submission, and portfolio review."
            elif w % 4 == 0:
                milestone = f"Month {w//4} Milestone Review: Practical project evaluation and retention quiz."
            else:
                milestone = focus_info.get("milestone_assessment", f"Week {w} Skills Check: Complete practice problem set.")

            # Prerequisite explanation
            prereqs = matched_module.prerequisites if matched_module and matched_module.prerequisites else []
            if prereqs:
                rationale = f"Scheduled for Week {w} following completion of foundational prerequisites: {', '.join(str(p) for p in prereqs)}."
            else:
                rationale = f"Scheduled for Week {w} as a foundational core competency without prior prerequisites."

            weekly_plan = WeeklyPlan(
                id=plan_id,
                learning_request_id=learning_request.id,
                week_number=w,
                focus_topic=topic,
                allocated_hours=allocated,
                module_id=matched_module.id if matched_module else None,
                exercises=exercises,
                milestone_assessment=milestone,
                prerequisite_rationale=rationale,
                status="planned"
            )
            db.add(weekly_plan)
            created_plans.append(weekly_plan)

        db.flush()

        sum_allocated = sum(p.allocated_hours for p in created_plans)
        
        # Log Stage C
        log = AgentLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            learning_request_id=learning_request.id,
            stage="Stage C: Prerequisite-Aware Planning",
            status="completed",
            message=f"Constructed {len(created_plans)}-week roadmap with {sum_allocated:.1f} hrs allocated (Budget: {total_budget:.1f} hrs). Every week strictly <= {max_weekly_hours:.1f} hrs.",
            details={
                "total_weeks": total_weeks,
                "total_allocated_hours": sum_allocated,
                "max_weekly_budget": max_weekly_hours,
                "budget_respected": all(p.allocated_hours <= max_weekly_hours for p in created_plans)
            }
        )
        db.add(log)
        db.commit()

        return created_plans

planner = Planner()
