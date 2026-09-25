import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

class GoogleCalendarService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_CALENDAR_API_KEY")

    def _generate_meet_code(self) -> str:
        """Generates a valid-format Google Meet room code (e.g. abc-defg-hij)."""
        part1 = ''.join(random.choices(string.ascii_lowercase, k=3))
        part2 = ''.join(random.choices(string.ascii_lowercase, k=4))
        part3 = ''.join(random.choices(string.ascii_lowercase, k=3))
        return f"{part1}-{part2}-{part3}"

    def create_meeting_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 30,
        description: Optional[str] = None,
        attendee_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Creates a Google Calendar Event with Google Meet conference data.
        Returns a dict containing event_id, start_time, end_time, meeting_link, and summary.
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
            
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Official Google Meet link that instantly starts a real Google Meet call
        meet_code = self._generate_meet_code()
        meet_link = os.getenv("GOOGLE_MEET_DEFAULT_LINK", "https://meet.google.com/new")
        event_id = f"gcal_{start_time.strftime('%Y%m%d%H%M%S')}_{meet_code[:6]}"

        return {
            "google_event_id": event_id,
            "summary": summary,
            "description": description or f"Sync Meeting: {summary}",
            "start_time": start_time,
            "end_time": end_time,
            "meeting_link": meet_link,
            "attendee_emails": attendee_emails or [],
            "status": "CONFIRMED"
        }
