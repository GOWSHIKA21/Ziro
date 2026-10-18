import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

# ----------------- Request Schemas -----------------

class LearningRequestCreate(BaseModel):
    goal: str = Field(..., min_length=3, max_length=255, description="Learning goal or target job role")
    starting_level: str = Field(default="Beginner", description="Beginner, Intermediate, or Advanced")
    weekly_hours: float = Field(..., gt=0, le=80, description="Available study hours per week")
    duration_value: int = Field(..., gt=0, le=104, description="Duration quantity")
    duration_unit: str = Field(default="months", description="'weeks' or 'months'")
    preferred_format: Optional[str] = Field(default="Mixed", description="Videos, Interactive courses, Documentation, or Mixed")

    @field_validator("goal")
    def validate_goal(cls, v):
        cleaned = v.strip() if v else ""
        if not cleaned or len(cleaned) < 3:
            raise ValueError("Goal must contain at least 3 non-whitespace characters.")
        return cleaned

    @field_validator("starting_level")
    def validate_level(cls, v):
        allowed = ["Beginner", "Intermediate", "Advanced"]
        if v.capitalize() not in allowed:
            raise ValueError(f"Starting level must be one of {allowed}")
        return v.capitalize()

    @field_validator("duration_unit")
    def validate_unit(cls, v):
        allowed = ["weeks", "months"]
        if v.lower() not in allowed:
            raise ValueError(f"Duration unit must be one of {allowed}")
        return v.lower()

    @field_validator("preferred_format")
    def validate_format(cls, v):
        if not v:
            return "Mixed"
        allowed = ["Videos", "Interactive courses", "Documentation", "Mixed"]
        matched = [a for a in allowed if a.lower() == v.lower()]
        if not matched:
            return "Mixed"
        return matched[0]


class ActionDecisionRequest(BaseModel):
    decision: str = Field(..., description="'approve' or 'reject'")
    notes: Optional[str] = Field(default=None)

    @field_validator("decision")
    def validate_decision(cls, v):
        if v.lower() not in ["approve", "reject"]:
            raise ValueError("Decision must be 'approve' or 'reject'")
        return v.lower()


class ActionEditRequest(BaseModel):
    title: Optional[str] = None
    schedule_details: Optional[Dict[str, Any]] = None


class ResourceReplaceRequest(BaseModel):
    reason: Optional[str] = "Manual replacement requested by user"


class CalendarSyncRequest(BaseModel):
    learning_request_id: str


class TestRunCreate(BaseModel):
    scenario_id: str = Field(..., description="TC1, TC2, TC3, TC4, or ALL")


# ----------------- Response Schemas -----------------

class VerificationEvidenceSchema(BaseModel):
    id: str
    resource_id: str
    check_timestamp: datetime.datetime
    http_status: Optional[int]
    pricing_indicators: Dict[str, Any]
    evidence_text: Optional[str]
    verification_type: str
    result_status: str

    class Config:
        from_attributes = True


class ResourceSchema(BaseModel):
    id: str
    learning_request_id: str
    module_id: Optional[str]
    title: str
    provider: str
    original_url: str
    skills_covered: List[str]
    estimated_hours: float
    prerequisites: List[str]
    free_status: str
    account_required: bool
    evidence_url: Optional[str]
    retrieval_timestamp: datetime.datetime
    verification_status: str
    verification_notes: Optional[str]
    is_replacement: bool
    replaces_resource_id: Optional[str]
    evidence_history: List[VerificationEvidenceSchema] = []

    class Config:
        from_attributes = True


class StudySessionSchema(BaseModel):
    id: str
    learning_request_id: str
    weekly_plan_id: Optional[str]
    title: str
    week_number: int
    scheduled_date: str
    start_time: str
    end_time: str
    duration_hours: float
    status: str
    calendar_event_id: Optional[str]
    is_user_created: bool
    idempotency_hash: str
    google_calendar_url: Optional[str] = None

    class Config:
        from_attributes = True


class WeeklyPlanSchema(BaseModel):
    id: str
    learning_request_id: str
    week_number: int
    focus_topic: str
    allocated_hours: float
    module_id: Optional[str]
    exercises: List[str]
    milestone_assessment: Optional[str]
    status: str
    study_sessions: List[StudySessionSchema] = []

    class Config:
        from_attributes = True


class LearningModuleSchema(BaseModel):
    id: str
    learning_request_id: str
    title: str
    description: Optional[str]
    order_index: int
    prerequisites: List[str]
    skills_covered: List[str]
    learning_outcomes: List[str]
    estimated_hours: float
    status: str

    class Config:
        from_attributes = True


class ProposedActionSchema(BaseModel):
    id: str
    learning_request_id: str
    action_type: str
    title: str
    description: str
    destination: str
    schedule_details: Dict[str, Any]
    requires_permissions: Optional[str]
    approval_status: str
    decision_timestamp: Optional[datetime.datetime]
    decision_notes: Optional[str]
    execution_status: str
    execution_result: Optional[Dict[str, Any]]
    idempotency_key: str
    executed_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class AgentLogSchema(BaseModel):
    id: str
    learning_request_id: str
    stage: str
    status: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class LearningRequestResponse(BaseModel):
    id: str
    goal: str
    starting_level: str
    weekly_hours: float
    duration_weeks: int
    duration_unit: str
    total_available_hours: float
    preferred_format: str
    status: str
    feasibility_status: str
    feasibility_notes: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    modules: List[LearningModuleSchema] = []
    weekly_plans: List[WeeklyPlanSchema] = []
    resources: List[ResourceSchema] = []
    proposed_actions: List[ProposedActionSchema] = []
    study_sessions: List[StudySessionSchema] = []
    agent_logs: List[AgentLogSchema] = []

    class Config:
        from_attributes = True


class TestRunResponse(BaseModel):
    id: str
    scenario_id: str
    scenario_name: str
    status: str
    input_data: Dict[str, Any]
    expected_result: str
    actual_result: str
    verification_evidence: Dict[str, Any]
    execution_duration_ms: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True
