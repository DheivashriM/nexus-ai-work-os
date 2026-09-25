import re
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.email_item import EmailItem
from app.models.user import User
from app.schemas.email_item import EmailSimulateRequest
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService
from app.services.blocker_service import BlockerService
from app.schemas.task import TaskCreate
from app.schemas.blocker import BlockerCreate

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def _analyze_email_with_ai(self, subject: str, body: str, sender_name: Optional[str] = None) -> tuple[str, str, str, str]:
        """
        Analyzes subject and body to determine: (urgency, category, ai_summary, ai_draft_reply)
        """
        content_lower = f"{subject} {body}".lower()

        # Extract clean greeting name (e.g., "Dheivashri M" -> "Dheivashri", or "john@acme.com" -> "John")
        greeting_name = "there"
        if sender_name:
            clean = sender_name.split("<")[0].strip('"\' ')
            parts = clean.split()
            if parts and len(parts[0]) > 1:
                greeting_name = parts[0].capitalize()

        # Urgency classification
        if any(w in content_lower for w in ["critical", "down", "outage", "broken", "emergency", "asap", "production failure", "crash"]):
            urgency = "CRITICAL"
        elif any(w in content_lower for w in ["bug", "error", "urgent", "failed", "issue", "payment", "delay"]):
            urgency = "HIGH"
        elif any(w in content_lower for w in ["meeting", "sync", "schedule", "call", "discussion"]):
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        # Category classification
        if any(w in content_lower for w in ["bug", "error", "broken", "issue"]):
            category = "CLIENT_BUG"
        elif any(w in content_lower for w in ["meet", "sync", "schedule", "calendar", "call"]):
            category = "MEETING_REQUEST"
        elif any(w in content_lower for w in ["approve", "sign", "review", "permission"]):
            category = "APPROVAL"
        else:
            category = "GENERAL"

        # AI Summary
        ai_summary = f"Incoming {urgency} email regarding '{subject}'. Category: {category}."

        # AI Draft Reply Generation
        if category == "CLIENT_BUG":
            ai_draft_reply = (
                f"Hi {greeting_name},\n\n"
                f"Thank you for reporting this issue regarding '{subject}'. Our engineering team has logged this as a {urgency} priority item and is investigating immediately.\n\n"
                f"We will update you as soon as a fix is deployed.\n\nBest regards,\nNexus Project Team"
            )
        elif category == "MEETING_REQUEST":
            ai_draft_reply = (
                f"Hi {greeting_name},\n\n"
                f"Thanks for reaching out about '{subject}'. I would be glad to schedule a sync. "
                f"Please let me know if tomorrow at 10:00 AM or 2:00 PM works for you.\n\nBest regards,\nNexus Project Team"
            )
        elif category == "APPROVAL":
            ai_draft_reply = (
                f"Hi {greeting_name},\n\n"
                f"Thank you for sending over '{subject}'. I am reviewing the details now and will provide approval shortly.\n\nBest regards,\nNexus Project Team"
            )
        else:
            ai_draft_reply = (
                f"Hi {greeting_name},\n\n"
                f"Thank you for your email regarding '{subject}'. We have received your message and will get back to you shortly.\n\nBest regards,\nNexus Project Team"
            )

        return urgency, category, ai_summary, ai_draft_reply

    def process_incoming_email(self, req: EmailSimulateRequest, target_user: User) -> EmailItem:
        """Processes an incoming email, runs AI classification, drafts a reply, and alerts user."""
        urgency, category, summary, draft_reply = self._analyze_email_with_ai(req.subject, req.body)

        email_item = EmailItem(
            user_id=target_user.id,
            sender=req.sender,
            sender_email=req.sender_email,
            subject=req.subject,
            body=req.body,
            urgency=urgency,
            category=category,
            ai_summary=summary,
            ai_draft_reply=draft_reply,
            status="UNREAD"
        )

        self.db.add(email_item)
        self.db.commit()
        self.db.refresh(email_item)

        # Alert user via Notification if Urgent
        if urgency in ("CRITICAL", "HIGH"):
            self.notification_service.create_notification(
                user_id=target_user.id,
                type="URGENT_EMAIL_RECEIVED",
                title=f"🚨 Urgent Email from {req.sender}: {req.subject}",
                message=f"Urgency: {urgency}. AI has prepared a draft reply for your review."
            )

        return email_item

    def get_user_emails(self, user_id: str, urgency_filter: Optional[str] = None) -> List[EmailItem]:
        query = self.db.query(EmailItem).filter(EmailItem.user_id == user_id)
        if urgency_filter:
            query = query.filter(EmailItem.urgency == urgency_filter.upper())
        return query.order_by(EmailItem.created_at.desc()).all()

    def send_ai_reply(self, email_id: str, user_id: str, custom_reply: Optional[str] = None, target_recipient_email: Optional[str] = None) -> EmailItem:
        email = self.db.query(EmailItem).filter(EmailItem.id == email_id, EmailItem.user_id == user_id).first()
        if not email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

        recipient = target_recipient_email or email.sender_email
        reply_to_send = custom_reply or email.ai_draft_reply or "Thank you for your email."

        from app.services.email_connection_service import EmailConnectionService
        address, password = EmailConnectionService.credentials(
            self.db.query(User).filter(User.id == user_id).first()
        )
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = address
            msg["To"] = recipient
            msg["Subject"] = f"Re: {email.subject}"
            msg.attach(MIMEText(reply_to_send, "plain"))

            with smtplib.SMTP(
                self.db.query(User).filter(User.id == user_id).first().email_smtp_host,
                self.db.query(User).filter(User.id == user_id).first().email_smtp_port,
                timeout=10,
            ) as server:
                server.starttls()
                server.login(address, password)
                server.send_message(msg)
        except Exception as smtperr:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Email provider rejected the reply") from smtperr

        email.status = "ACTIONED"
        self.db.commit()

        # Log Notification of Sent Email
        self.notification_service.create_notification(
            user_id=user_id,
            type="EMAIL_REPLIED",
            title=f"✉️ Reply Sent to {recipient}",
            message=f"Sent AI Reply for '{email.subject}'"
        )
        return email

    def convert_email_to_task(self, email_id: str, user_id: str, project_id: str) -> dict:
        email = self.db.query(EmailItem).filter(EmailItem.id == email_id, EmailItem.user_id == user_id).first()
        if not email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

        task_service = TaskService(self.db)
        priority_map = {"CRITICAL": "URGENT", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}
        task_in = TaskCreate(
            project_id=project_id,
            title=f"Email: {email.subject}",
            description=f"From: {email.sender} ({email.sender_email})\n\n{email.body}",
            priority=priority_map.get(email.urgency, "MEDIUM"),
            assignee_id=user_id
        )
        user = self.db.query(User).filter(User.id == user_id).first()
        task = task_service.create_task(task_in, user)

        email.status = "ACTIONED"
        self.db.commit()
        return {"message": f"Successfully created Task '{task.title}'", "task_id": task.id}

    def sync_real_gmail_inbox(self, target_user: User, limit: int = 10) -> List[EmailItem]:
        """
        Connects to Gmail via IMAP SSL (imap.gmail.com:993), fetches recent real emails from inbox,
        runs AI urgency classification and draft generation, and saves to database.
        """
        from app.services.email_connection_service import EmailConnectionService
        address, password = EmailConnectionService.credentials(target_user)

        import imaplib
        import email as email_parser
        from email.header import decode_header

        synced_items = []
        try:
            mail = imaplib.IMAP4_SSL(target_user.email_imap_host, target_user.email_imap_port)
            mail.login(address, password)
            mail.select("inbox")

            status_code, data = mail.search(None, "ALL")
            if status_code != "OK" or not data[0]:
                mail.logout()
                return []

            email_ids = data[0].split()
            recent_ids = email_ids[-limit:]  # Get last N emails

            for e_id in reversed(recent_ids):
                res_code, msg_data = mail.fetch(e_id, "(RFC822)")
                if res_code != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email_parser.message_from_bytes(response_part[1])
                        subject_header = msg.get("Subject", "(No Subject)")
                        decoded_subj = ""
                        for part, encoding in decode_header(subject_header):
                            if isinstance(part, bytes):
                                decoded_subj += part.decode(encoding or "utf-8", errors="ignore")
                            else:
                                decoded_subj += str(part)

                        from_header = msg.get("From", address)
                        sender_name = from_header
                        sender_email = from_header
                        if "<" in from_header and ">" in from_header:
                            sender_name = from_header.split("<")[0].strip('" ')
                            sender_email = from_header.split("<")[1].split(">")[0]

                        # Extract text body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors="ignore")
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")

                        body = body.strip() or f"Email received from {sender_name}"

                        # Check if email already exists in DB to prevent duplicates
                        existing = self.db.query(EmailItem).filter(
                            EmailItem.user_id == target_user.id,
                            EmailItem.subject == decoded_subj,
                            EmailItem.sender_email == sender_email
                        ).first()

                        if existing:
                            continue

                        # Run AI Analysis
                        urgency, category, ai_summary, ai_draft_reply = self._analyze_email_with_ai(decoded_subj, body)

                        email_item = EmailItem(
                            user_id=target_user.id,
                            sender=sender_name or sender_email,
                            sender_email=sender_email,
                            subject=decoded_subj,
                            body=body[:2000],  # store up to 2000 chars
                            urgency=urgency,
                            category=category,
                            ai_summary=ai_summary,
                            ai_draft_reply=ai_draft_reply,
                            status="UNREAD"
                        )
                        self.db.add(email_item)
                        synced_items.append(email_item)

            self.db.commit()
            mail.logout()
        except Exception as e:
            print(f"[EmailService] Real Gmail IMAP fetch error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch Gmail inbox: {e}")

        return synced_items
