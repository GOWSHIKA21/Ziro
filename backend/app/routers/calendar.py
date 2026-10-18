"""
Calendar REST API Router
Provides access to scheduled study sessions, universal RFC 5545 iCalendar (.ics) exports,
one-click Google Calendar web links, interactive session completion toggling,
and custom session creation for user event preservation testing.
"""

import uuid
import hashlib
import datetime
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import StudySession, LearningRequest, User, utc_now
from ..schemas import (
    StudySessionSchema, StudySessionProgressUpdate,
    GoogleCalendarStatusResponse, GoogleCalendarAuthUrlResponse
)
from ..services.auth_service import (
    get_current_user, get_current_user_optional,
    get_guest_session_id_optional, verify_learning_path_access
)
from ..services.google_calendar_service import google_calendar_oauth
from ..config import settings

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


class UserSessionCreate(BaseModel):
    learning_request_id: str
    title: str
    scheduled_date: str  # YYYY-MM-DD
    start_time: str      # HH:MM
    end_time: str        # HH:MM
    duration_hours: float

def build_google_calendar_url(session: StudySession) -> str:
    """Builds a zero-friction Google Calendar web template URL for one-click add."""
    try:
        clean_date = session.scheduled_date.replace("-", "")
        clean_start = session.start_time.replace(":", "") + "00"
        clean_end = session.end_time.replace(":", "") + "00"
        dates_param = f"{clean_date}T{clean_start}/{clean_date}T{clean_end}"
        params = {
            "action": "TEMPLATE",
            "text": session.title,
            "dates": dates_param,
            "details": f"Week {session.week_number} focused study block allocated by Free Learning Path Builder AI Agent.",
            "location": "Online / Focused Study"
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    except Exception:
        return ""

def attach_google_url(session: StudySession) -> StudySessionSchema:
    schema = StudySessionSchema.model_validate(session)
    schema.google_calendar_url = build_google_calendar_url(session)
    return schema

@router.get("/sessions", response_model=List[StudySessionSchema])
def list_calendar_sessions(
    learning_request_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """List scheduled calendar study sessions with security isolation."""
    query = db.query(StudySession)
    if learning_request_id:
        req = db.query(LearningRequest).filter(LearningRequest.id == learning_request_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Learning path not found.")
        verify_learning_path_access(req, current_user, guest_session_id)
        query = query.filter(StudySession.learning_request_id == learning_request_id)
    elif current_user:
        query = query.join(LearningRequest).filter(LearningRequest.user_id == current_user.id)
    elif guest_session_id:
        query = query.join(LearningRequest).filter(LearningRequest.guest_session_id == guest_session_id)
    else:
        return []

    sessions = query.order_by(StudySession.scheduled_date.asc(), StudySession.start_time.asc()).all()
    return [attach_google_url(s) for s in sessions]


@router.get("/export-ics")
def export_icalendar(
    learning_request_id: str = Query(..., description="ID of the learning path to export"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Universal RFC 5545 iCalendar (.ics) export.
    Can be imported with a single click into Apple Calendar, Google Calendar, and Microsoft Outlook.
    """
    req = db.query(LearningRequest).filter(LearningRequest.id == learning_request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    verify_learning_path_access(req, current_user, guest_session_id)

    sessions = db.query(StudySession).filter(
        StudySession.learning_request_id == learning_request_id
    ).order_by(StudySession.scheduled_date.asc()).all()

    now_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Free Learning Path Builder//Autonomous AI Agent//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{req.goal} - Study Schedule"
    ]

    for s in sessions:
        try:
            start_fmt = s.scheduled_date.replace("-", "") + "T" + s.start_time.replace(":", "") + "00"
            end_fmt = s.scheduled_date.replace("-", "") + "T" + s.end_time.replace(":", "") + "00"
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{s.idempotency_hash}@freelearningpath.ai",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{start_fmt}",
                f"DTEND:{end_fmt}",
                f"SUMMARY:{s.title}",
                f"DESCRIPTION:Week {s.week_number} focused session for {req.goal} ({s.duration_hours}h). Allocated by AI Agent.",
                "LOCATION:Focused Study Environment",
                "STATUS:CONFIRMED",
                "END:VEVENT"
            ])
        except Exception:
            continue

    ics_lines.append("END:VCALENDAR")
    content = "\r\n".join(ics_lines)

    filename = f"study_plan_{req.id}.ics"
    return Response(
        content=content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache"
        }
    )


@router.post("/sessions/{id}/toggle-complete", response_model=StudySessionSchema)
def toggle_session_complete(
    id: str,
    payload: Optional[StudySessionProgressUpdate] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Toggles session status between 'synced_calendar' and 'completed'
    and optionally logs actual study minutes, notes, and timestamp.
    """
    session = db.query(StudySession).filter(StudySession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.learning_request:
        verify_learning_path_access(session.learning_request, current_user, guest_session_id, is_mutation=True)

    if payload:
        session.status = "completed" if payload.is_completed else "synced_calendar"
        if payload.actual_minutes_studied is not None:
            session.actual_minutes_studied = payload.actual_minutes_studied
        if payload.study_notes is not None:
            session.study_notes = payload.study_notes
        if payload.is_completed:
            session.completed_at = utc_now()
        else:
            session.completed_at = None
    else:
        if session.status != "completed":
            session.status = "completed"
            session.completed_at = utc_now()
            if not session.actual_minutes_studied:
                session.actual_minutes_studied = int(session.duration_hours * 60)
        else:
            session.status = "synced_calendar"
            session.completed_at = None

    db.commit()
    db.refresh(session)
    return attach_google_url(session)


@router.post("/sessions", response_model=StudySessionSchema, status_code=201)
def create_user_session(
    payload: UserSessionCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """
    Create a user-defined custom study session.
    Marked with is_user_created=True to verify that agent synchronization
    strictly preserves user events without overwriting or deleting them.
    """
    req = db.query(LearningRequest).filter(LearningRequest.id == payload.learning_request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Learning path not found.")

    verify_learning_path_access(req, current_user, guest_session_id, is_mutation=True)

    hash_raw = f"{payload.learning_request_id}:{payload.scheduled_date}:{payload.start_time}:user"
    sess_hash = hashlib.sha256(hash_raw.encode()).hexdigest()[:24]

    existing = db.query(StudySession).filter(StudySession.idempotency_hash == sess_hash).first()
    if existing:
        return attach_google_url(existing)

    session_id = f"sess_user_{uuid.uuid4().hex[:10]}"
    session = StudySession(
        id=session_id,
        learning_request_id=payload.learning_request_id,
        weekly_plan_id=None,
        title=payload.title,
        week_number=1,
        scheduled_date=payload.scheduled_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_hours=payload.duration_hours,
        status="synced_calendar",
        calendar_event_id=f"evt_user_{sess_hash[:10]}",
        is_user_created=True,
        idempotency_hash=sess_hash
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return attach_google_url(session)


@router.delete("/sessions/{id}")
def delete_session(
    id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    guest_session_id: Optional[str] = Depends(get_guest_session_id_optional),
    db: Session = Depends(get_db)
):
    """Delete a study session from the calendar."""
    session = db.query(StudySession).filter(StudySession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.learning_request:
        verify_learning_path_access(session.learning_request, current_user, guest_session_id, is_mutation=True, is_delete=True)

    db.delete(session)
    db.commit()
    return {"deleted": True, "id": id}


# ----------------- Google Calendar OAuth 2.0 Endpoints -----------------

@router.get("/oauth/status", response_model=GoogleCalendarStatusResponse)
def get_calendar_oauth_status(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns the Google Calendar OAuth connection status for the authenticated user.
    """
    client_configured = google_calendar_oauth.is_configured()
    if not current_user:
        return {
            "is_connected": False,
            "calendar_email": None,
            "connected_at": None,
            "client_id_configured": client_configured,
            "scope": None
        }

    is_connected = bool(current_user.google_calendar_refresh_token)
    return {
        "is_connected": is_connected,
        "calendar_email": current_user.google_calendar_email,
        "connected_at": current_user.google_calendar_connected_at,
        "client_id_configured": client_configured,
        "scope": current_user.google_calendar_scope
    }


@router.get("/oauth/authorize", response_model=GoogleCalendarAuthUrlResponse)
def authorize_google_calendar(
    redirect_to: Optional[str] = Query(None, description="Frontend page to return to upon OAuth completion"),
    current_user: User = Depends(get_current_user)
):
    """
    Generates the Google OAuth 2.0 authorization URL:
    - Requests minimal 'calendar.events' scope (avoids full calendar management)
    - Uses offline access ('access_type=offline') and 'prompt=consent' to ensure refresh_token generation
    - Generates a signed CSRF state parameter bound to current_user.id
    - Enforces the exact registered callback URI
    """
    auth_data = google_calendar_oauth.generate_authorization_url(
        user_id=current_user.id,
        redirect_to=redirect_to
    )
    return auth_data


@router.get("/oauth/callback")
def google_calendar_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 Callback handler:
    1. Validates the state parameter against CSRF attacks.
    2. Exchanges authorization code securely for tokens.
    3. Fetches the connected Google user account email.
    4. Persists the refresh token (strictly preserving any existing refresh token if Google does not return a new one).
    5. Redirects back to the frontend with confirmation parameter.
    """
    if error:
        target = f"{settings.FRONTEND_URL}/?calendar_error={urllib.parse.quote(error)}"
        return RedirectResponse(url=target, status_code=303)

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required code or state parameter."
        )

    # 1. Cryptographically validate state token
    state_payload = google_calendar_oauth.verify_oauth_state(state)
    user_id = state_payload.get("sub")
    redirect_to = state_payload.get("redirect_to") or settings.FRONTEND_URL

    # 2. Look up the initiating user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this OAuth session was not found."
        )

    # 3. Securely exchange code for tokens
    token_data = google_calendar_oauth.exchange_code_for_tokens(code)
    access_token = token_data.get("access_token")

    # 4. Fetch associated Google account email for display
    google_email = None
    if access_token:
        google_email = google_calendar_oauth.fetch_google_account_email(access_token)

    # 5. Persist tokens (preserving existing refresh token if none returned)
    google_calendar_oauth.save_user_tokens(db, user, token_data, google_email=google_email)

    # 6. Redirect to frontend with success flag
    delimiter = "&" if "?" in redirect_to else "?"
    final_redirect = f"{redirect_to}{delimiter}calendar_connected=true"
    return RedirectResponse(url=final_redirect, status_code=303)


@router.post("/oauth/disconnect")
def disconnect_google_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnects the user's Google Calendar:
    Revokes the token at Google and removes all credentials from the persistent database.
    """
    return google_calendar_oauth.disconnect_calendar(db, current_user)

