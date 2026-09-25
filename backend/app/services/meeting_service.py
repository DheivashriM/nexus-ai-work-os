from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import re

from app.models.user import User
from app.models.meeting import Meeting
from app.models.activity import Activity
from app.services.notification_service import NotificationService
from app.tools.entity_resolver import EntityResolver
from app.integrations.google_calendar import GoogleCalendarService

class MeetingService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.google_calendar_service = GoogleCalendarService()

    def parse_datetime_expression(self, time_str: str) -> datetime:
        """Parses natural time expressions like 'today 6pm', 'tomorrow 10am', '2026-09-15 18:00' or ISO strings into datetime in UTC."""
        if not time_str or not time_str.strip():
            time_str = "today 6pm"

        raw_str = time_str.strip()
        local_tz = datetime.now().astimezone().tzinfo or timezone.utc
        now_local = datetime.now(local_tz)

        # 1. Direct ISO format check (e.g. "2026-09-15T18:00:00" or "2026-09-15 18:00")
        if len(raw_str) >= 10 and raw_str[4] == '-' and raw_str[7] == '-':
            try:
                iso_candidate = raw_str.replace(" ", "T")
                dt = datetime.fromisoformat(iso_candidate)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=local_tz)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

        clean_str = raw_str.lower()

        # 2. Determine target date
        target_date = now_local.date()
        if "tomorrow" in clean_str:
            target_date = (now_local + timedelta(days=1)).date()
        elif "today" in clean_str:
            target_date = now_local.date()
        else:
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', clean_str)
            if date_match:
                target_date = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))).date()

        # 3. Extract time components safely without matching year numbers (like 2026)
        time_part_str = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_str).strip()
        time_part_str = re.sub(r'today|tomorrow', '', time_part_str).strip()

        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)?', time_part_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(4)

            if meridiem:
                if meridiem == "pm" and hour < 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
            elif hour < 8 and "pm" not in clean_str and "am" not in clean_str:
                # Default evening times like 6 to 18:00
                hour += 12

            local_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=local_tz)
            return local_dt.astimezone(timezone.utc)

        # Fallback: now_local + 1 hour
        fallback_dt = (now_local + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return fallback_dt.astimezone(timezone.utc)

    def schedule_meeting(
        self,
        organizer: User,
        attendee_query: str,
        title: Optional[str] = None,
        date_time_str: Optional[str] = None,
        duration_minutes: int = 30,
        description: Optional[str] = None
    ) -> Tuple[Optional[Meeting], Optional[str]]:
        """
        Schedules a meeting, creates Google Meet link, saves to DB, and sends notifications to all attendees.
        """
        # Resolve target attendee
        attendee_user, candidates, err = EntityResolver.resolve_user(self.db, attendee_query)
        if err or not attendee_user:
            candidate_names = [u.name for u in candidates] if candidates else []
            return None, f"Could not resolve attendee '{attendee_query}'. Candidates: {candidate_names}"

        # Parse start time
        start_time = self.parse_datetime_expression(date_time_str or "today 6pm")
        
        meeting_title = title or f"Sync Meeting with {attendee_user.name}"

        # Generate Google Meet link and event details
        gcal_data = self.google_calendar_service.create_meeting_event(
            summary=meeting_title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            description=description,
            attendee_emails=[organizer.email, attendee_user.email]
        )

        attendee_ids = list({organizer.id, attendee_user.id})

        meeting = Meeting(
            title=meeting_title,
            description=description or f"Scheduled meeting between {organizer.name} and {attendee_user.name}.",
            start_time=gcal_data["start_time"],
            end_time=gcal_data["end_time"],
            meeting_link=gcal_data["meeting_link"],
            google_event_id=gcal_data["google_event_id"],
            organizer_id=organizer.id,
            attendee_ids=attendee_ids
        )

        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)

        # Send Notifications to all attendees (including target user)
        local_start = start_time.astimezone() if start_time.tzinfo else start_time
        formatted_time = local_start.strftime("%b %d, %Y at %I:%M %p")
        notif_msg = (
            f"📅 You have a meeting scheduled with {organizer.name} for {formatted_time}.\n"
            f"🔗 Join Google Meet: {gcal_data['meeting_link']}"
        )

        for u_id in attendee_ids:
            self.notification_service.create_notification(
                user_id=u_id,
                type="MEETING_SCHEDULED",
                title=f"Meeting Scheduled: {meeting_title}",
                message=notif_msg
            )

        # Add Activity audit log
        activity = Activity(
            user_id=organizer.id,
            activity_type="SCHEDULED_MEETING",
            description=f"Scheduled meeting '{meeting_title}' with {attendee_user.name}.",
            metadata_json={
                "title": meeting_title,
                "attendee": attendee_user.name,
                "start_time": str(start_time),
                "meeting_link": gcal_data["meeting_link"]
            }
        )
        self.db.add(activity)
        self.db.commit()

        # Dispatch Authenticated n8n Webhook Automation
        try:
            from app.services.n8n_service import N8nService
            N8nService.dispatch_event_async(
                event_type="MEETING_SCHEDULED",
                data={
                    "meeting_id": meeting.id,
                    "title": meeting_title,
                    "organizer": organizer.name,
                    "organizer_email": organizer.email,
                    "attendee": attendee_user.name,
                    "attendee_email": attendee_user.email,
                    "start_time": str(start_time),
                    "meeting_link": gcal_data["meeting_link"]
                }
            )
        except Exception as e:
            print("[MeetingService] n8n dispatch error:", e)

        return meeting, None

    def get_user_meetings(self, user_id: str) -> List[Meeting]:
        """Gets all upcoming meetings where user is organizer or attendee."""
        meetings = self.db.query(Meeting).order_by(Meeting.start_time.asc()).all()
        return [m for m in meetings if m.organizer_id == user_id or (m.attendee_ids and user_id in m.attendee_ids)]
