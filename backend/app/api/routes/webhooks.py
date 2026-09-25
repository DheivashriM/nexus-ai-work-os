from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.get("/health")
def webhook_health():
    return {"status": "active", "message": "Webhook service operational"}


