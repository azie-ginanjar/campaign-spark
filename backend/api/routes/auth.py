import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Response
from backend.core.dependencies import get_redis_repo
from backend.core.config import settings
from backend.repositories.redis_repo import RedisRepository

router = APIRouter()

class EmailSchema(BaseModel):
    email: EmailStr

JWT_SECRET = settings.lemonsqueezy_webhook_secret.get_secret_value()

@router.post("/auth/request-magic-link")
def request_magic_link(
    request: EmailSchema,
    repo: RedisRepository = Depends(get_redis_repo)
):
    if not repo.is_premium(request.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No premium account found for this email."
        )
        
    token = repo.store_magic_link(request.email)
    
    print(f"\n========== MAGIC LINK GENERATED ==========")
    print(f"Email: {request.email}")
    print(f"Link: http://localhost:8000/api/v1/auth/verify?token={token}")
    print(f"==========================================\n")
    
    return {"status": "success", "message": "Magic link sent to email if account exists."}

@router.get("/auth/verify")
def verify_magic_link(
    token: str,
    response: Response,
    repo: RedisRepository = Depends(get_redis_repo)
):
    email = repo.verify_magic_link(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token."
        )
        
    expiration = datetime.now(timezone.utc) + timedelta(days=30)
    jwt_payload = {
        "sub": email,
        "exp": expiration,
        "premium": True
    }
    encoded_jwt = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")
    
    response.set_cookie(
        key="session_token",
        value=encoded_jwt,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60
    )
    
    return {"status": "success", "message": "Authenticated successfully. Cookie set."}
