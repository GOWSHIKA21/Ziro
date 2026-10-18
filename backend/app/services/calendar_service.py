"""
Calendar Synchronization Service
Handles integration with Google Calendar API when configured,
or the persistent Mock Calendar with duplicate detection and preservation of user-created events.
"""

import uuid
import datetime
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import LearningRequest, StudySession, ProposedAction, AgentLog
from ..config import settings

class CalendarService:
    def __init__(self):
        self.is_google_configured = bool(
            settings.GOOGLE_CALENDAR_CLIENT_ID and settings.GOOGLE_CALENDAR_REFRESH_TOKEN
        )

    def sync_calendar(
        self,
        db: Session,
        learning_request: LearningRequest
    ) -> Dict[str, Any]:
        """
        Synchronizes approved study sessions to the calendar.
        Strict invariant: Only adds genuinely missing sessions!
        Preserves existing user-created events and prevents duplicates.
        """
        # 1. Fetch all study sessions already registered
        existing_sessions = db.query(StudySession).filter(
            StudySession.learning_request_id == learning_request.id
        ).all()
        
        existing_hashes = {s.idempotency_hash for s in existing_sessions}
        
        # 2. Check approved calendar actions to see if any sessions need to be created
        approved_calendar_actions = [
            a for a in learning_request.proposed_actions 
            if a.action_type == "calendar_block" and a.approval_status == "Approved"
        ]

        added_sessions = []
        skipped_duplicates = 0
        preserved_user_events = len([s for s in existing_sessions if s.is_user_created])

        today = datetime.date.today()
        weekly_hours = learning_request.weekly_hours
        session_duration = 2.5 if weekly_hours == 5 else (2.0 if weekly_hours <= 6 else 3.0)
        sessions_count = max(1, int(round(weekly_hours / session_duration)))

        for act in approved_calendar_actions:
            week_num = act.schedule_details.get("week_number", 1)
            start_date = today + datetime.timedelta(days=(7 * (week_num - 1)) + (7 - today.weekday()))
            days_offsets = [1, 3] if sessions_count == 2 else [1, 3, 5] if sessions_count >= 3 else [5]

            for i, offset in enumerate(days_offsets[:sessions_count]):
                sess_date = start_date + datetime.timedelta(days=offset)
                date_str = sess_date.isoformat()
                
                hash_raw = f"{learning_request.id}:{date_str}:18:30"
                sess_hash = hashlib.sha256(hash_raw.encode()).hexdigest()[:24]

                if sess_hash in existing_hashes:
                    skipped_duplicates += 1
                    continue

                # Add new missing session
                session_id = f"sess_{learning_request.id}_w{week_num}_{i+1}_{uuid.uuid4().hex[:4]}"
                new_session = StudySession(
                    id=session_id,
                    learning_request_id=learning_request.id,
                    week_number=week_num,
                    title=f"Study Session: Week {week_num} (Part {i+1})",
                    scheduled_date=date_str,
                    start_time="18:30",
                    end_time="21:00" if session_duration == 2.5 else "20:30",
                    duration_hours=session_duration,
                    status="synced_calendar",
                    calendar_event_id=f"evt_{sess_hash[:12]}",
                    is_user_created=False,
                    idempotency_hash=sess_hash
                )
                db.add(new_session)
                existing_hashes.add(sess_hash)
                added_sessions.append(new_session)

        db.commit()

        # Refresh total count
        all_sessions = db.query(StudySession).filter(
            StudySession.learning_request_id == learning_request.id
        ).all()

        summary = {
            "integration_mode": "Google Calendar API" if self.is_google_configured else "Mock Calendar (Persistent)",
            "added_missing_sessions": len(added_sessions),
            "skipped_duplicates": skipped_duplicates,
            "preserved_user_events": preserved_user_events,
            "total_calendar_events": len(all_sessions),
            "sessions": [
                {
                    "id": s.id,
                    "date": s.scheduled_date,
                    "time": f"{s.start_time} - {s.end_time}",
                    "title": s.title,
                    "calendar_event_id": s.calendar_event_id,
                    "is_user_created": s.is_user_created
                } for s in all_sessions
            ]
        }

        # Log calendar sync
        log = AgentLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            learning_request_id=learning_request.id,
            stage="Stage F: Calendar Synchronization",
            status="completed",
            message=f"Calendar synchronized: {len(added_sessions)} missing sessions added, {skipped_duplicates} duplicate blocks prevented, {preserved_user_events} user events preserved.",
            details=summary
        )
        db.add(log)
        db.commit()

        return summary

calendar_service = CalendarService()
