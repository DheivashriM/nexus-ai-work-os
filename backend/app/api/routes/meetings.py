from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Meetings"])

class MeetingScheduleRequest(BaseModel):
    attendee: str = Field(..., description="Name, email, or user identifier of attendee (e.g., 'Selva')")
    title: Optional[str] = Field(None, description="Meeting title/topic")
    date_time: Optional[str] = Field("today 6pm", description="Time expression e.g. 'today 6pm'")
    duration_minutes: Optional[int] = Field(30, description="Duration in minutes")
    description: Optional[str] = Field(None, description="Optional description")

from datetime import datetime, timezone

def format_dt_iso(dt: datetime) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

class MeetingResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    meeting_link: str
    organizer_id: str
    attendee_ids: List[str]

    class Config:
        from_attributes = True

@router.post("/schedule", response_model=MeetingResponse)
def schedule_meeting(
    req: MeetingScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MeetingService(db)
    meeting, err = service.schedule_meeting(
        organizer=current_user,
        attendee_query=req.attendee,
        title=req.title,
        date_time_str=req.date_time,
        duration_minutes=req.duration_minutes or 30,
        description=req.description
    )
    if err or not meeting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "Failed to schedule meeting."
        )
    return MeetingResponse(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        start_time=format_dt_iso(meeting.start_time),
        end_time=format_dt_iso(meeting.end_time),
        meeting_link=meeting.meeting_link,
        organizer_id=meeting.organizer_id,
        attendee_ids=meeting.attendee_ids or []
    )

@router.get("", response_model=List[MeetingResponse])
def get_user_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MeetingService(db)
    meetings = service.get_user_meetings(current_user.id)
    return [
        MeetingResponse(
            id=m.id,
            title=m.title,
            description=m.description,
            start_time=format_dt_iso(m.start_time),
            end_time=format_dt_iso(m.end_time),
            meeting_link=m.meeting_link,
            organizer_id=m.organizer_id,
            attendee_ids=m.attendee_ids or []
        )
        for m in meetings
    ]

