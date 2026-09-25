from typing import Any

from app.core.config import settings
from app.integrations.whatsapp.meta.client import MetaWhatsAppClient, is_real_config_value
from app.integrations.whatsapp.meta.types import ProviderAccount


class MetaWhatsAppProvider:
    """Nexus-facing adapter for Meta WhatsApp Cloud API."""

    def __init__(self, client: MetaWhatsAppClient | None = None, phone_number_id: str | None = None, access_token: str | None = None):
        self.client = client or MetaWhatsAppClient(phone_number_id, access_token)

    def get_connection_status(self) -> list[ProviderAccount]:
        account = self.client.get_phone_number()
        return [ProviderAccount(provider_account_id=str(account.get("id")), phone_number=account.get("display_phone_number"), display_name=account.get("verified_name"), status="connected")]

    def send_text_message(self, recipient_phone: str, body: str) -> str:
        return self.client.send_text_message(recipient_phone, body)

    def webhook_configuration(self, webhook_url: str) -> dict[str, Any]:
        return {"url": webhook_url, "verify_token_configured": is_real_config_value(settings.META_WA_VERIFY_TOKEN), "subscribe_fields": ["messages"], "note": "Configure the callback URL and verify token in Meta Developers, then subscribe the messages field."}