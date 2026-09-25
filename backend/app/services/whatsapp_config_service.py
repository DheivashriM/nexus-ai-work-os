from sqlalchemy.orm import Session

from app.core.credential_crypto import decrypt_secret, encrypt_secret
from app.models.whatsapp import WhatsAppConfiguration


class WhatsAppConfigService:
    @staticmethod
    def get(db: Session) -> WhatsAppConfiguration | None:
        return db.query(WhatsAppConfiguration).filter(WhatsAppConfiguration.workspace_id == "default").first()

    @staticmethod
    def credentials(db: Session) -> dict[str, str]:
        config = WhatsAppConfigService.get(db)
        if not config or not config.phone_number_id or not config.access_token_encrypted:
            return {}
        return {
            "phone_number_id": config.phone_number_id,
            "access_token": decrypt_secret(config.access_token_encrypted),
            "app_secret": decrypt_secret(config.app_secret_encrypted) if config.app_secret_encrypted else "",
            "verify_token": decrypt_secret(config.verify_token_encrypted) if config.verify_token_encrypted else "",
            "public_api_url": config.public_api_url or "",
        }

    @staticmethod
    def save(db: Session, phone_number_id: str, access_token: str, app_secret: str, verify_token: str, public_api_url: str) -> WhatsAppConfiguration:
        config = WhatsAppConfigService.get(db)
        if not config:
            config = WhatsAppConfiguration(workspace_id="default")
            db.add(config)
        config.phone_number_id = phone_number_id.strip()
        config.access_token_encrypted = encrypt_secret(access_token.strip())
        config.app_secret_encrypted = encrypt_secret(app_secret.strip()) if app_secret.strip() else None
        config.verify_token_encrypted = encrypt_secret(verify_token.strip())
        config.public_api_url = public_api_url.strip().rstrip("/")
        db.commit()
        db.refresh(config)
        return config