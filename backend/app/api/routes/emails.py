from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.email_item import EmailItemResponse, EmailSimulateRequest, SendEmailReplyRequest
from app.services.email_service import EmailService

router = APIRouter(prefix="/emails", tags=["Smart Email Assistant"])

@router.get("", response_model=List[EmailItemResponse])
def get_emails(
    urgency: Optional[str] = Query(None, description="Filter by urgency e.g. CRITICAL, HIGH, MEDIUM, LOW"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = EmailService(db)
    items = service.get_user_emails(current_user.id, urgency_filter=urgency)
    return [
        EmailItemResponse(
            id=item.id,
            user_id=item.user_id,
            sender=item.sender,
            sender_email=item.sender_email,
            subject=item.subject,
            body=item.body,
            urgency=item.urgency,
            category=item.category,
            ai_summary=item.ai_summary,
            ai_draft_reply=item.ai_draft_reply,
            status=item.status,
            created_at=str(item.created_at)
        )
        for item in items
    ]

@router.post("/simulate", response_model=EmailItemResponse, status_code=status.HTTP_201_CREATED)
def simulate_incoming_email(
    req: EmailSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulates receiving an incoming email and running AI urgency analysis & draft generation."""
    service = EmailService(db)
    item = service.process_incoming_email(req, current_user)
    return EmailItemResponse(
        id=item.id,
        user_id=item.user_id,
        sender=item.sender,
        sender_email=item.sender_email,
        subject=item.subject,
        body=item.body,
        urgency=item.urgency,
        category=item.category,
        ai_summary=item.ai_summary,
        ai_draft_reply=item.ai_draft_reply,
        status=item.status,
        created_at=str(item.created_at)
    )

@router.post("/{email_id}/reply")
def send_email_reply(
    email_id: str,
    req: SendEmailReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approves and dispatches the AI-generated email reply."""
    service = EmailService(db)
    item = service.send_ai_reply(
        email_id,
        current_user.id,
        custom_reply=req.reply_body,
        target_recipient_email=req.recipient_email
    )
    return {"message": f"Reply successfully sent to {req.recipient_email or item.sender_email}", "email_id": item.id}

@router.post("/{email_id}/convert-task")
def convert_email_to_task(
    email_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Converts an email into a PM Tool Task."""
    service = EmailService(db)
    return service.convert_email_to_task(email_id, current_user.id, project_id)

@router.post("/sync-gmail", response_model=List[EmailItemResponse])
def sync_real_gmail_inbox(
    limit: int = Query(10, description="Max emails to fetch from Gmail inbox"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Connects to real Gmail inbox via IMAP SSL and syncs recent emails with AI urgency analysis."""
    service = EmailService(db)
    items = service.sync_real_gmail_inbox(current_user, limit=limit)
    return [
        EmailItemResponse(
            id=item.id,
            user_id=item.user_id,
            sender=item.sender,
            sender_email=item.sender_email,
            subject=item.subject,
            body=item.body,
            urgency=item.urgency,
            category=item.category,
            ai_summary=item.ai_summary,
            ai_draft_reply=item.ai_draft_reply,
            status=item.status,
            created_at=str(item.created_at)
        )
        for item in items
    ]
