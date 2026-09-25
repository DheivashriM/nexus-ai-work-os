import hashlib
import hmac
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_authenticated_user
from app.core.config import settings
from app.core.database import get_db
from app.integrations.whatsapp.meta.client import MetaWhatsAppClient, MetaWhatsAppError, is_real_config_value
from app.integrations.whatsapp.meta.provider import MetaWhatsAppProvider
from app.integrations.whatsapp.meta.service import WORKSPACE_ID, persist_message, process_meta_webhook, sync_provider_data
from app.integrations.whatsapp.meta.types import ProviderMessage
from app.models.user import User
from app.models.whatsapp import WhatsAppAccount, WhatsAppConversation, WhatsAppMessage
from app.schemas.whatsapp import WhatsAppAccountRead, WhatsAppConfigRead, WhatsAppConfigUpdate, WhatsAppConversationRead, WhatsAppMessageRead, WhatsAppSendText, WhatsAppStatusRead
from app.services.whatsapp_config_service import WhatsAppConfigService

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Inbox"])


def admin_user(user: User = Depends(get_authenticated_user)) -> User:
    if user.role not in {"ADMIN", "MANAGER"}:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def configured_credentials(db: Session) -> dict[str, str]:
    stored = WhatsAppConfigService.credentials(db)
    if stored:
        return stored
    if is_real_config_value(settings.META_WA_ACCESS_TOKEN) and is_real_config_value(settings.META_WA_PHONE_NUMBER_ID):
        return {"phone_number_id": settings.META_WA_PHONE_NUMBER_ID, "access_token": settings.META_WA_ACCESS_TOKEN, "app_secret": settings.META_APP_SECRET, "verify_token": settings.META_WA_VERIFY_TOKEN, "public_api_url": settings.NEXUS_PUBLIC_API_URL}
    return {}


@router.get("/admin/config", response_model=WhatsAppConfigRead)
def get_config(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    credentials = configured_credentials(db)
    public_url = credentials.get("public_api_url") or settings.NEXUS_PUBLIC_API_URL
    return {"configured": bool(credentials), "phone_number_id": credentials.get("phone_number_id"), "public_api_url": public_url, "webhook_url": f"{public_url}/api/whatsapp/webhook" if public_url else None}


@router.put("/admin/config", response_model=WhatsAppConfigRead)
def save_config(data: WhatsAppConfigUpdate, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    WhatsAppConfigService.save(db, data.phone_number_id, data.access_token, data.app_secret, data.verify_token, data.public_api_url)
    return get_config(_, db)


@router.get("/status", response_model=WhatsAppStatusRead)
def get_status(_: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    accounts = db.query(WhatsAppAccount).filter(WhatsAppAccount.workspace_id == WORKSPACE_ID).all()
    credentials = configured_credentials(db)
    try:
        provider_accounts = MetaWhatsAppProvider(phone_number_id=credentials.get("phone_number_id"), access_token=credentials.get("access_token")).get_connection_status()
        for provider_account in provider_accounts:
            existing = next((account for account in accounts if account.provider_account_id == provider_account.provider_account_id), None)
            if not existing:
                existing = WhatsAppAccount(workspace_id=WORKSPACE_ID, provider="meta", provider_account_id=provider_account.provider_account_id)
                db.add(existing)
                accounts.append(existing)
            existing.phone_number = provider_account.phone_number
            existing.display_name = provider_account.display_name
            existing.status = "connected" if provider_account.status == "active" else "disconnected"
        db.commit()
    except MetaWhatsAppError:
        configured = bool(credentials)
        return {"configured": configured, "connected": False, "status": "error" if configured else "not_configured", "accounts": accounts}
    connected = any(account.status == "connected" for account in accounts)
    return {"configured": bool(credentials), "connected": connected, "status": "connected" if connected else "disconnected", "accounts": accounts}


@router.post("/sync", response_model=dict)
def sync_whatsapp(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    try:
        return sync_provider_data(db)
    except MetaWhatsAppError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/admin/webhooks", response_model=dict)
def configure_webhooks(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    credentials = configured_credentials(db)
    if not credentials:
        raise HTTPException(status_code=400, detail="Meta WhatsApp Cloud API is not configured")
    try:
        url = f"{credentials.get('public_api_url') or settings.NEXUS_PUBLIC_API_URL.rstrip('/')}/api/whatsapp/webhook"
        return MetaWhatsAppProvider().webhook_configuration(url)
    except MetaWhatsAppError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/conversations", response_model=List[WhatsAppConversationRead])
def list_conversations(_: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    return db.query(WhatsAppConversation).filter(WhatsAppConversation.workspace_id == WORKSPACE_ID).order_by(WhatsAppConversation.last_message_at.desc().nullslast()).all()


@router.get("/conversations/{conversation_id}/messages", response_model=List[WhatsAppMessageRead])
def list_messages(conversation_id: str, _: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    conversation = db.query(WhatsAppConversation).filter(WhatsAppConversation.id == conversation_id, WhatsAppConversation.workspace_id == WORKSPACE_ID).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="WhatsApp conversation not found")
    return db.query(WhatsAppMessage).filter(WhatsAppMessage.whatsapp_conversation_id == conversation.id, WhatsAppMessage.workspace_id == WORKSPACE_ID).order_by(WhatsAppMessage.provider_timestamp.asc()).all()


@router.post("/conversations/{conversation_id}/messages", response_model=WhatsAppMessageRead)
def send_message(conversation_id: str, data: WhatsAppSendText, _: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    conversation = db.query(WhatsAppConversation).filter(WhatsAppConversation.id == conversation_id, WhatsAppConversation.workspace_id == WORKSPACE_ID).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="WhatsApp conversation not found")
    try:
        credentials = configured_credentials(db)
        uid = MetaWhatsAppProvider(phone_number_id=credentials.get("phone_number_id"), access_token=credentials.get("access_token")).send_text_message(conversation.external_conversation_id, data.body.strip())
    except MetaWhatsAppError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    message = persist_message(db, ProviderMessage(uid=uid, chat_id=conversation.external_conversation_id, from_me=True, text=data.body.strip(), status="pending"), None)
    if not message:
        raise HTTPException(status_code=502, detail="Meta WhatsApp returned an invalid message ID")
    return message


@router.get("/webhook", include_in_schema=False)
def verify_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    credentials = configured_credentials(db)
    verify_token = credentials.get("verify_token") or settings.META_WA_VERIFY_TOKEN
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and hmac.compare_digest(params.get("hub.verify_token", ""), verify_token):
        return int(params.get("hub.challenge", "0"))
    raise HTTPException(status_code=403, detail="Invalid Meta webhook verification")


@router.post("/webhook", include_in_schema=False)
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    credentials = configured_credentials(db)
    app_secret = credentials.get("app_secret") or settings.META_APP_SECRET
    if is_real_config_value(app_secret):
        signature = request.headers.get("x-hub-signature-256", "")
        body = await request.body()
        expected = "sha256=" + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")
        try:
            payload = __import__("json").loads(body)
        except Exception:
            return {"status": "ignored", "reason": "invalid_json"}
    else:
        try:
            payload = await request.json()
        except Exception:
            return {"status": "ignored", "reason": "invalid_json"}
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored", "reason": "malformed_event"}
    background_tasks.add_task(process_meta_webhook, payload)
    return {"status": "accepted"}