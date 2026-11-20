import time
import hmac
import hashlib
import threading
from typing import Generator, Optional, List, Dict
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.core.security import decode_token
from app.core.config import settings
from app.models.models import User, AuditLog, RevokedToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

# In-memory replay protection cache for agent nonces
_nonce_lock = threading.Lock()
_seen_nonces: Dict[str, float] = {}


def _cleanup_old_nonces(max_age_seconds: int = 600):
    now = time.time()
    with _nonce_lock:
        to_remove = [n for n, ts in _seen_nonces.items() if now - ts > max_age_seconds]
        for n in to_remove:
            del _seen_nonces[n]


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    jti = payload.get("jti")
    if jti:
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user no longer exists",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
        
    return user


def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles} roles. Current role is {current_user.role}",
            )
        return current_user
    return role_checker


async def verify_agent_token(
    request: Request,
    x_agent_signature: Optional[str] = Header(None),
    x_agent_timestamp: Optional[str] = Header(None),
    x_agent_nonce: Optional[str] = Header(None),
    x_agent_secret: Optional[str] = Header(None)
) -> bool:
    """
    Validates agent telemetry with HMAC signature, timestamp window, and nonce replay check.
    Supports backward-compatible secret matching in development/test mode.
    """
    now = time.time()
    
    # Check HMAC signature headers
    if x_agent_signature and x_agent_timestamp and x_agent_nonce:
        try:
            req_ts = float(x_agent_timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp header format",
            )
            
        # 1. Enforce 5-minute sliding window (timestamp validation)
        if abs(now - req_ts) > 300:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent timestamp expired or clock skew too high (must be within 300s)",
            )

        # 2. Enforce Replay Protection via Nonce check
        _cleanup_old_nonces(max_age_seconds=600)
        with _nonce_lock:
            if x_agent_nonce in _seen_nonces:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Replay attack detected: nonce has already been processed",
                )
            _seen_nonces[x_agent_nonce] = now

        # 3. Compute and verify HMAC-SHA256 signature
        body_bytes = await request.body()
        message = f"{x_agent_timestamp}:{x_agent_nonce}:".encode("utf-8") + body_bytes
        expected_sig = hmac.new(
            settings.AGENT_SHARED_SECRET.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(x_agent_signature.lower(), expected_sig.lower()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC agent signature",
            )
        return True

    # Fallback for development / test mode with direct secret
    if x_agent_secret:
        valid_dev_secrets = {
            settings.AGENT_SHARED_SECRET,
            "sentinel_agent_telemetry_secure_key_2026",
            "sentinel_dev_agent_telemetry_secure_key_2026"
        }
        if x_agent_secret in valid_dev_secrets:
            if settings.ENVIRONMENT.lower() == "production":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="HMAC signature headers required in production mode",
                )
            return True

    # If neither HMAC nor valid secret provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized agent: missing or invalid authentication credentials",
    )


def log_audit(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None
):
    ip_address = None
    if request and request.client:
        ip_address = request.client.host

    # Sanitize details to never record passwords, tokens, or credentials
    sanitized_details = None
    if details:
        SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "hashed_password"}
        sanitized_details = {
            k: ("***REDACTED***" if k.lower() in SENSITIVE_KEYS else v)
            for k, v in details.items()
        }

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=sanitized_details,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
