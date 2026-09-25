from typing import Any

import requests

from app.core.config import settings


def is_real_config_value(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(normalized) and not normalized.startswith(("your_", "replace_", "change_me"))


class MetaWhatsAppError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MetaWhatsAppClient:
    def __init__(self, phone_number_id: str | None = None, access_token: str | None = None):
        self.phone_number_id = phone_number_id or settings.META_WA_PHONE_NUMBER_ID
        self.access_token = access_token or settings.META_WA_ACCESS_TOKEN
        self.base_url = settings.META_WA_API_BASE_URL.rstrip("/")

    def request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if not is_real_config_value(self.access_token) or not is_real_config_value(self.phone_number_id):
            raise MetaWhatsAppError("Meta WhatsApp Cloud API is not configured")
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            response = requests.request(method, f"{self.base_url}{path}", headers=headers, timeout=15, **kwargs)
        except requests.RequestException as exc:
            raise MetaWhatsAppError("Meta WhatsApp Cloud API is unavailable") from exc
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not response.ok:
            error = payload.get("error", {})
            raise MetaWhatsAppError(error.get("message") or f"Meta WhatsApp request failed ({response.status_code})", response.status_code)
        return payload

    def get_phone_number(self) -> dict[str, Any]:
        return self.request("GET", f"/{self.phone_number_id}", params={"fields": "display_phone_number,verified_name,quality_rating"})

    def send_text_message(self, recipient_phone: str, body: str) -> str:
        payload = self.request("POST", f"/{self.phone_number_id}/messages", json={"messaging_product": "whatsapp", "to": recipient_phone, "type": "text", "text": {"preview_url": False, "body": body}})
        message_id = (payload.get("messages") or [{}])[0].get("id")
        if not message_id:
            raise MetaWhatsAppError("Meta WhatsApp did not return a message ID")
        return str(message_id)