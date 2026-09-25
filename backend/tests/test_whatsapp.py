from app.integrations.whatsapp.meta.service import persist_message
from app.integrations.whatsapp.meta.types import ProviderMessage
from app.models.whatsapp import WhatsAppMessage


def test_whatsapp_api_requires_authentication(client):
    response = client.get("/api/whatsapp/status")
    assert response.status_code == 401


def test_whatsapp_message_uid_is_idempotent(db_session):
    provider_message = ProviderMessage(
        uid="provider-message-1",
        chat_id="123",
        sender_phone="+15551230000",
        sender_name="Customer",
        text="Hello",
        timestamp="2026-09-24T10:00:00Z",
    )
    first = persist_message(db_session, provider_message, "account-1")
    second = persist_message(db_session, provider_message, "account-1")

    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert db_session.query(WhatsAppMessage).count() == 1
