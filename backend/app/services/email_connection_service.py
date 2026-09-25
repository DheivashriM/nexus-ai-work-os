import imaplib
import smtplib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.credential_crypto import decrypt_secret, encrypt_secret
from app.models.user import User
from app.schemas.email_settings import EmailSettingsRead, EmailSettingsUpdate


class EmailConnectionService:
    @staticmethod
    def read_settings(user: User) -> EmailSettingsRead:
        return EmailSettingsRead(
            configured=bool(user.email_address and user.email_password_encrypted),
            enabled=bool(user.email_connection_enabled),
            email_address=user.email_address,
            imap_host=user.email_imap_host,
            imap_port=user.email_imap_port,
            smtp_host=user.email_smtp_host,
            smtp_port=user.email_smtp_port,
        )

    @staticmethod
    def save_settings(db: Session, user: User, data: EmailSettingsUpdate) -> EmailSettingsRead:
        user.email_connection_enabled = data.enabled
        user.email_address = str(data.email_address)
        user.email_imap_host = data.imap_host.strip()
        user.email_imap_port = data.imap_port
        user.email_smtp_host = data.smtp_host.strip()
        user.email_smtp_port = data.smtp_port
        user.email_password_encrypted = encrypt_secret(data.password)
        db.commit()
        db.refresh(user)
        return EmailConnectionService.read_settings(user)

    @staticmethod
    def credentials(user: User) -> tuple[str, str]:
        if not user.email_connection_enabled or not user.email_address or not user.email_password_encrypted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configure and enable your email connection first")
        try:
            return user.email_address, decrypt_secret(user.email_password_encrypted)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    @staticmethod
    def test_connection(user: User) -> None:
        address, password = EmailConnectionService.credentials(user)
        try:
            with imaplib.IMAP4_SSL(user.email_imap_host, user.email_imap_port) as mail:
                mail.login(address, password)
                mail.logout()
            with smtplib.SMTP(user.email_smtp_host, user.email_smtp_port, timeout=10) as server:
                server.starttls()
                server.login(address, password)
        except Exception as exc:
            raise ValueError("Email connection failed. Check the address, app password, hosts, ports, and provider security settings.") from exc