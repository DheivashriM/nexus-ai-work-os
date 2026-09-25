from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.websocket_manager import ws_manager
from app.integrations.whatsapp.meta.provider import MetaWhatsAppProvider
from app.integrations.whatsapp.meta.types import ProviderMessage
from app.models.whatsapp import WhatsAppAccount, WhatsAppConversation, WhatsAppMessage
from app.services.whatsapp_config_service import WhatsAppConfigService

WORKSPACE_ID = "default"


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def upsert_account(db: Session, account_id: str, phone: str | None = None, name: str | None = None, status: str = "pending") -> WhatsAppAccount:
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.workspace_id == WORKSPACE_ID, WhatsAppAccount.provider_account_id == account_id).first()
    if not account:
        account = WhatsAppAccount(workspace_id=WORKSPACE_ID, provider="meta", provider_account_id=account_id)
        db.add(account)
    account.provider = "meta"
    account.phone_number = phone or account.phone_number
    account.display_name = name or account.display_name
    account.status = status.lower()
    now = datetime.now(timezone.utc)
    if account.status == "connected":
        account.last_connected_at = now
    if account.status == "disconnected":
        account.last_disconnected_at = now
    db.flush()
    return account


def persist_message(db: Session, provider_message: ProviderMessage, account_id: str | None = None) -> WhatsAppMessage | None:
    existing = db.query(WhatsAppMessage).filter(WhatsAppMessage.workspace_id == WORKSPACE_ID, WhatsAppMessage.external_message_id == provider_message.uid).first()
    if existing:
        if provider_message.status:
            existing.status = provider_message.status.lower()
            db.commit()
        return existing
    conversation = db.query(WhatsAppConversation).filter(WhatsAppConversation.workspace_id == WORKSPACE_ID, WhatsAppConversation.external_conversation_id == provider_message.chat_id).first()
    if not conversation:
        account = upsert_account(db, account_id or "unknown", provider_message.recipient_phone, status="connected")
        conversation = WhatsAppConversation(workspace_id=WORKSPACE_ID, whatsapp_account_id=account.id, external_conversation_id=provider_message.chat_id, contact_phone=provider_message.sender_phone, contact_name=provider_message.sender_name)
        db.add(conversation)
        db.flush()
    direction = "outgoing" if provider_message.from_me else "incoming"
    message = WhatsAppMessage(workspace_id=WORKSPACE_ID, whatsapp_conversation_id=conversation.id, external_message_id=provider_message.uid, direction=direction, sender_phone=provider_message.sender_phone, sender_name=provider_message.sender_name, message_type="text" if provider_message.text is not None else provider_message.message_type.lower(), body=provider_message.text, provider_timestamp=parse_timestamp(provider_message.timestamp or provider_message.received_timestamp), status=(provider_message.status or "pending").lower(), media_metadata=provider_message.data or None)
    db.add(message)
    conversation.last_message_at = message.provider_timestamp
    conversation.last_message_preview = message.body
    if direction == "incoming":
        conversation.unread_count += 1
    db.commit()
    db.refresh(message)
    return message


def serialize_message(message: WhatsAppMessage) -> dict[str, Any]:
    return {"id": message.id, "conversation_id": message.whatsapp_conversation_id, "external_message_id": message.external_message_id, "direction": message.direction, "body": message.body, "message_type": message.message_type, "status": message.status, "provider_timestamp": message.provider_timestamp.isoformat()}


async def process_meta_webhook(payload: dict[str, Any]) -> None:
    with SessionLocal() as db:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                account_id = metadata.get("phone_number_id")
                contacts = {item.get("wa_id"): item for item in value.get("contacts", [])}
                for item in value.get("messages", []):
                    sender_phone = item.get("from")
                    contact = contacts.get(sender_phone, {})
                    text = item.get("text", {}).get("body") if item.get("type") == "text" else None
                    message = persist_message(db, ProviderMessage(uid=item["id"], chat_id=sender_phone, sender_phone=sender_phone, sender_name=contact.get("profile", {}).get("name"), recipient_phone=metadata.get("display_phone_number"), text=text, timestamp=item.get("timestamp"), message_type=item.get("type", "unknown"), data=item), account_id)
                    if message:
                        event = {"event": "whatsapp.message.created", "message": serialize_message(message)}
                        for user_id in ws_manager.get_online_users():
                            await ws_manager.send_personal_message(event, user_id)
                for status in value.get("statuses", []):
                    message = db.query(WhatsAppMessage).filter(WhatsAppMessage.external_message_id == status.get("id"), WhatsAppMessage.workspace_id == WORKSPACE_ID).first()
                    if message:
                        message.status = status.get("status", message.status)
                        db.commit()


def sync_provider_data(db: Session) -> dict[str, int]:
    credentials = WhatsAppConfigService.credentials(db)
    account = MetaWhatsAppProvider(phone_number_id=credentials.get("phone_number_id"), access_token=credentials.get("access_token")).get_connection_status()[0]
    upsert_account(db, account.provider_account_id, account.phone_number, account.display_name, "connected")
    db.commit()
    return {"accounts": 1, "conversations": 0, "messages": 0}