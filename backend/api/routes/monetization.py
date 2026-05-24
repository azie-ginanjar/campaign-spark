import hmac
import hashlib
from fastapi import APIRouter, Depends, Request, HTTPException, status
from backend.core.dependencies import get_redis_repo
from backend.core.config import settings
from backend.repositories.redis_repo import RedisRepository

router = APIRouter()

@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    repo: RedisRepository = Depends(get_redis_repo)
):
    # 1. Read raw body and signature
    raw_body = await request.body()
    signature = request.headers.get("x-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # 2. Verify HMAC-SHA256 signature
    secret = settings.lemonsqueezy_webhook_secret.get_secret_value().encode('utf-8')
    computed_signature = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # 3. Parse JSON payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 4. Extract email and set premium status
    meta = payload.get("meta", {})
    custom_data = meta.get("custom_data", {})
    email = custom_data.get("email")
    
    if not email:
        data = payload.get("data", {}).get("attributes", {})
        email = data.get("user_email")

    if not email:
        return {"status": "ignored", "reason": "No email found in payload"}
        
    repo.set_premium(email)
    
    return {"status": "success", "message": f"Premium activated for {email}"}
