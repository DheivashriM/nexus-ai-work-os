import hmac
import hashlib
import json
import time
import requests
import threading
from typing import Dict, Any, Optional
from app.core.config import settings

class N8nService:
    """
    Production-grade, authenticated Webhook Dispatcher for n8n Automation Engine.
    All outgoing webhooks are cryptographically signed using HMAC SHA-256.
    """

    @staticmethod
    def _generate_hmac_signature(payload_str: str, secret: str) -> str:
        """Generates an HMAC SHA-256 signature for payload verification."""
        return hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    def dispatch_event_async(cls, event_type: str, data: Dict[str, Any], webhook_url: Optional[str] = None):
        """Dispatches event payload to n8n in a non-blocking background thread."""
        thread = threading.Thread(
            target=cls.dispatch_event,
            args=(event_type, data, webhook_url),
            daemon=True
        )
        thread.start()

    @classmethod
    def dispatch_event(cls, event_type: str, data: Dict[str, Any], webhook_url: Optional[str] = None) -> bool:
        """
        Sends an authenticated webhook payload to n8n with timestamp and signature headers.
        """
        url = webhook_url or settings.N8N_WEBHOOK_URL
        if not url:
            return False

        timestamp = str(int(time.time()))
        payload = {
            "event_type": event_type,
            "timestamp": timestamp,
            "data": data
        }

        payload_json = json.dumps(payload, sort_keys=True)
        signature = cls._generate_hmac_signature(payload_json, settings.N8N_WEBHOOK_SECRET)

        headers = {
            "Content-Type": "application/json",
            "X-PMTool-Signature": signature,
            "X-PMTool-Timestamp": timestamp,
            "X-PMTool-Event": event_type,
            "User-Agent": "PMTool-Backend-Security/1.0"
        }

        try:
            response = requests.post(url, data=payload_json, headers=headers, timeout=5)
            return response.status_code in (200, 201, 202)
        except Exception as e:
            # Log failure silently without interrupting main application flow
            print(f"[N8nService] Webhook dispatch warning for {event_type}: {e}")
            return False
