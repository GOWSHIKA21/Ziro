import datetime

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False, default="")
    avatar_url = Column(String(512), nullable=True)
    google_id = Column(String(128), unique=True, nullable=True, index=True)
    auth_provider = Column(String(32), default="email")  # "email", "google"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Google Calendar OAuth 2.0 Credentials & State
    google_calendar_refresh_token = Column(Text, nullable=True)
    google_calendar_access_token = Column(Text, nullable=True)
    google_calendar_token_expiry = Column(DateTime, nullable=True)
    google_calendar_email = Column(String(255), nullable=True)
    google_calendar_connected_at = Column(DateTime, nullable=True)
    google_calendar_scope = Column(String(255), nullable=True)

    learning_requests = relationship("LearningRequest", back_populates="user", cascade="all, delete-orphan")



class LearningRequest(Base):
    __tablename__ = "learning_requests"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    goal = Column(String(255), nullable=False)
    starting_level = Column(String(32), default="Beginner")  # Beginner, Intermediate, Advanced
    weekly_hours = Column(Float, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    duration_unit = Column(String(16), default="weeks")  # weeks or months
    total_available_hours = Column(Float, nullable=False)
    preferred_format = Column(String(32), default="Mixed")  # Videos, Interactive courses, Documentation, Mixed
    
    status = Column(String(32), default="created")  # created, analyzed, planned, verified, active, completed
    feasibility_status = Column(String(32), default="feasible")  # feasible, constrained_scope, unfeasible
    feasibility_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="learning_requests")
    modules = relationship("LearningModule", back_populates="learning_request", cascade="all, delete-orphan", order_by="LearningModule.order_index")
    weekly_plans = relationship("WeeklyPlan", back_populates="learning_request", cascade="all, delete-orphan", order_by="WeeklyPlan.week_number")
    resources = relationship("Resource", back_populates="learning_request", cascade="all, delete-orphan")
    proposed_actions = relationship("ProposedAction", back_populates="learning_request", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="learning_request", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="learning_request", cascade="all, delete-orphan", order_by="AgentLog.timestamp")
    adaptive_revisions = relationship("AdaptiveRevision", back_populates="learning_request", cascade="all, delete-orphan", order_by="AdaptiveRevision.timestamp.desc()")


class LearningModule(Base):
    __tablename__ = "learning_modules"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    prerequisites = Column(JSON, default=list)  # list of prerequisite module titles / IDs
    skills_covered = Column(JSON, default=list)
    learning_outcomes = Column(JSON, default=list)
    estimated_hours = Column(Float, default=0.0)
    status = Column(String(32), default="pending")  # pending, in_progress, completed

    learning_request = relationship("LearningRequest", back_populates="modules")
    weekly_plans = relationship("WeeklyPlan", back_populates="module")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    focus_topic = Column(String(255), nullable=False)
    allocated_hours = Column(Float, nullable=False)
    module_id = Column(String(64), ForeignKey("learning_modules.id"), nullable=True)
    exercises = Column(JSON, default=list)
    milestone_assessment = Column(Text, nullable=True)
    status = Column(String(32), default="planned")  # planned, current, completed

    learning_request = relationship("LearningRequest", back_populates="weekly_plans")
    module = relationship("LearningModule", back_populates="weekly_plans")
    study_sessions = relationship("StudySession", back_populates="weekly_plan", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    module_id = Column(String(64), nullable=True)
    title = Column(String(255), nullable=False)
    provider = Column(String(128), nullable=False)
    original_url = Column(Text, nullable=False)
    skills_covered = Column(JSON, default=list)
    estimated_hours = Column(Float, default=0.0)
    prerequisites = Column(JSON, default=list)
    free_status = Column(String(32), default="unverified")  # verified_free, possibly_free, paid, broken, unverified
    account_required = Column(Boolean, default=False)
    evidence_url = Column(Text, nullable=True)
    retrieval_timestamp = Column(DateTime, default=utc_now)
    verification_status = Column(String(32), default="unverified")  # verified, flagged, failed, unverified
    verification_notes = Column(Text, nullable=True)
    
    is_replacement = Column(Boolean, default=False)
    replaces_resource_id = Column(String(64), nullable=True)

    learning_request = relationship("LearningRequest", back_populates="resources")
    evidence_history = relationship("VerificationEvidence", back_populates="resource", cascade="all, delete-orphan", order_by="VerificationEvidence.check_timestamp.desc()")


class VerificationEvidence(Base):
    __tablename__ = "verification_evidence"

    id = Column(String(64), primary_key=True, index=True)
    resource_id = Column(String(64), ForeignKey("resources.id"), nullable=False)
    check_timestamp = Column(DateTime, default=utc_now)
    http_status = Column(Integer, nullable=True)
    pricing_indicators = Column(JSON, default=dict)
    evidence_text = Column(Text, nullable=True)
    verification_type = Column(String(32), default="live_http")  # live_http, simulated_test, cached_profile
    result_status = Column(String(32), nullable=False)  # verified_free, paid_detected, broken_link, check_failed

    resource = relationship("Resource", back_populates="evidence_history")


class ProposedAction(Base):
    __tablename__ = "proposed_actions"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    action_type = Column(String(32), nullable=False)  # course_enrollment, calendar_block
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    destination = Column(Text, nullable=False)  # enrollment URL or calendar identifier
    schedule_details = Column(JSON, default=dict)
    requires_permissions = Column(Text, nullable=True)
    
    approval_status = Column(String(32), default="Pending Approval")  # Pending Approval, Approved, Rejected
    decision_timestamp = Column(DateTime, nullable=True)
    decision_notes = Column(Text, nullable=True)
    
    execution_status = Column(String(32), default="Pending")  # Pending, Executed, Verified, Failed
    execution_result = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    executed_at = Column(DateTime, nullable=True)

    learning_request = relationship("LearningRequest", back_populates="proposed_actions")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    weekly_plan_id = Column(String(64), ForeignKey("weekly_plans.id"), nullable=True)
    title = Column(String(255), nullable=False)
    week_number = Column(Integer, nullable=False)
    scheduled_date = Column(String(16), nullable=False)  # YYYY-MM-DD
    start_time = Column(String(8), nullable=False)       # HH:MM
    end_time = Column(String(8), nullable=False)         # HH:MM
    duration_hours = Column(Float, nullable=False)
    status = Column(String(32), default="scheduled")     # scheduled, synced_calendar, completed, cancelled
    calendar_event_id = Column(String(128), nullable=True)
    is_user_created = Column(Boolean, default=False)
    idempotency_hash = Column(String(128), unique=True, index=True, nullable=False)
    
    # Progress & Study logging
    actual_minutes_studied = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    study_notes = Column(Text, nullable=True)

    learning_request = relationship("LearningRequest", back_populates="study_sessions")
    weekly_plan = relationship("WeeklyPlan", back_populates="study_sessions")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    stage = Column(String(64), nullable=False)  # Stage A, Stage B, etc.
    status = Column(String(32), nullable=False)  # started, completed, failed, warning
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utc_now)

    learning_request = relationship("LearningRequest", back_populates="agent_logs")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(16), nullable=False, index=True)  # TC1, TC2, TC3, TC4
    scenario_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)  # passed, failed, running
    input_data = Column(JSON, default=dict)
    expected_result = Column(Text, nullable=False)
    actual_result = Column(Text, nullable=False)
    verification_evidence = Column(JSON, default=dict)
    execution_duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)


class AdaptiveRevision(Base):
    __tablename__ = "adaptive_revisions"

    id = Column(String(64), primary_key=True, index=True)
    learning_request_id = Column(String(64), ForeignKey("learning_requests.id"), nullable=False)
    revision_type = Column(String(64), nullable=False)  # missed_sessions, availability_change, pace_adjustment
    previous_state = Column(JSON, default=dict)
    adjusted_state = Column(JSON, default=dict)
    reasoning = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    learning_request = relationship("LearningRequest", back_populates="adaptive_revisions")
