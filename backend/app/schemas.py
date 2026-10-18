import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

# ----------------- Auth Schemas -----------------

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(default="", max_length=255, description="Full name or display name")

    @field_validator("email")
    def validate_email(cls, v):
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Invalid email format.")
        return cleaned

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("email")
    def validate_email(cls, v):
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    auth_provider: str = "email"
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token issued by Google Identity Services")


class GoogleConfigResponse(BaseModel):
    client_id: Optional[str] = None
    is_configured: bool = False


class GoogleCalendarStatusResponse(BaseModel):
    is_connected: bool
    calendar_email: Optional[str] = None
    connected_at: Optional[datetime.datetime] = None
    client_id_configured: bool = False
    scope: Optional[str] = None


class GoogleCalendarAuthUrlResponse(BaseModel):
    auth_url: str
    state: str
    redirect_uri: str
    scope: str


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
    actual_minutes_studied: int = 0
    completed_at: Optional[datetime.datetime] = None
    study_notes: Optional[str] = None

    class Config:
        from_attributes = True


class StudySessionProgressUpdate(BaseModel):
    is_completed: bool = True
    actual_minutes_studied: Optional[int] = Field(default=None, ge=0)
    study_notes: Optional[str] = Field(default=None, max_length=1000)



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


class AdaptiveRevisionSchema(BaseModel):
    id: str
    learning_request_id: str
    revision_type: str
    previous_state: Dict[str, Any] = {}
    adjusted_state: Dict[str, Any] = {}
    reasoning: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class AdaptivePlanRequest(BaseModel):
    new_weekly_hours: Optional[float] = Field(default=None, gt=0, le=80, description="Updated available weekly study hours")
    missed_strategy: str = Field(default="rebalance", description="'rebalance' (redistribute over remaining weeks) or 'extend' (add extra weeks)")
    pace_adjustment: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Pace multiplier (e.g. 0.8 for slower, 1.2 for faster)")


class AdaptivePlanResponse(BaseModel):
    revision_id: str
    learning_request_id: str
    message: str
    previous_hours: float
    new_hours: float
    adjusted_weeks_count: int
    reasoning: str


class LearningRequestResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
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
    adaptive_revisions: List[AdaptiveRevisionSchema] = []

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
