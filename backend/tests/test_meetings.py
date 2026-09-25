import pytest
from datetime import datetime, timezone
from app.services.meeting_service import MeetingService
from app.models.user import User

def test_parse_datetime_expressions(db_session):
    service = MeetingService(db_session)

    # 1. Test 'today 6pm'
    dt1 = service.parse_datetime_expression("today 6pm")
    assert dt1.tzinfo is not None
    assert dt1.tzinfo == timezone.utc

    # 2. Test 'tomorrow 10am'
    dt2 = service.parse_datetime_expression("tomorrow 10am")
    assert dt2.tzinfo is not None
    assert dt2.tzinfo == timezone.utc

    # 3. Test ISO string with date '2026-09-15 18:00'
    dt3 = service.parse_datetime_expression("2026-09-15 18:00")
    assert dt3.tzinfo is not None
    assert dt3.tzinfo == timezone.utc

def test_schedule_meeting_flow(db_session):
    service = MeetingService(db_session)
    organizer = User(name="Organizer", email="organizer@test.com", password_hash="hash")
    attendee = User(name="Sibi Chakravarthy", email="sibi@test.com", password_hash="hash")
    db_session.add(organizer)
    db_session.add(attendee)
    db_session.commit()

    meeting, err = service.schedule_meeting(
        organizer=organizer,
        attendee_query="Sibi",
        title="Architecture Sync",
        date_time_str="tomorrow 4pm",
        duration_minutes=30
    )

    assert err is None
    assert meeting is not None
    assert meeting.title == "Architecture Sync"
    assert meeting.start_time is not None
    assert meeting.end_time > meeting.start_time
