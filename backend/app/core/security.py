import os
import re
import time
import uuid
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Dict, List
import jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger("sentinelai.security")

# Configure password hashing with Argon2 and bcrypt
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Enforce enterprise password security standard:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one numeric digit
    - At least one special symbol
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters in length."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one numeric digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+~`\[\]/\\]", password):
        return False, "Password must contain at least one special character."
    return True, ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    token_jti = jti or str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "type": "access",
        "jti": token_jti
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
    token_jti = jti or str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": token_jti
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# Rate limiter for authentication & setup endpoints with Redis persistence and in-memory fallback
class AuthRateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.attempts: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_rate_limited(self, key: str) -> tuple[bool, int]:
        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_key = f"sentinel:ratelimit:{key}"
                pipe = redis_client.pipeline()
                pipe.incr(redis_key)
                pipe.ttl(redis_key)
                results = pipe.execute()
                count = results[0]
                ttl = results[1]

                if count == 1:
                    redis_client.expire(redis_key, self.window_seconds)

                if count > self.max_requests:
                    retry_after = ttl if ttl > 0 else self.window_seconds
                    return True, retry_after
                return False, 0
            except Exception as e:
                logger.warning(f"[AuthRateLimiter] Redis rate limiting error: {e}. Falling back to memory.")

        # In-memory sliding window fallback
        now = time.time()
        with self.lock:
            if key not in self.attempts:
                self.attempts[key] = []
            self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window_seconds]
            if len(self.attempts[key]) >= self.max_requests:
                oldest = self.attempts[key][0]
                retry_after = int(self.window_seconds - (now - oldest))
                return True, max(1, retry_after)
            self.attempts[key].append(now)
            return False, 0

    def reset(self, key: str):
        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_client.delete(f"sentinel:ratelimit:{key}")
            except Exception:
                pass

        with self.lock:
            if key in self.attempts:
                del self.attempts[key]


auth_rate_limiter = AuthRateLimiter(max_requests=5, window_seconds=60)
