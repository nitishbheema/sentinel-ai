import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, log_audit
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password_strength,
    auth_rate_limiter
)
from app.models.models import User, RevokedToken
from app.schemas.schemas import (
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserOut,
    UserCreate,
    UserUpdate,
    AdminSetupRequest,
    SetupStatusResponse
)

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@router.get("/setup-status", response_model=SetupStatusResponse)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Checks whether first-time administrator setup is required.
    """
    total_users = db.query(User).count()
    setup_required = total_users == 0
    return {
        "setup_required": setup_required,
        "user_count": total_users,
        "message": "First-time administrator setup required." if setup_required else "Platform already provisioned."
    }


@router.post("/setup-admin", response_model=TokenResponse)
def setup_initial_admin(
    admin_in: AdminSetupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Provisions the initial administrator during first-time platform initialization.
    Blocked permanently once any user exists in the database.
    """
    if db.query(User).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial administrator setup has already been completed. Login using existing credentials."
        )

    # Rate limiting on setup attempts
    client_ip = request.client.host if request.client else "unknown"
    limited, retry_after = auth_rate_limiter.is_rate_limited(f"setup_{client_ip}")
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many setup attempts. Please retry after {retry_after} seconds."
        )

    # Validate password complexity
    is_strong, reason = validate_password_strength(admin_in.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insecure password: {reason}"
        )

    admin_user = User(
        username=admin_in.username.strip(),
        email=admin_in.email.strip().lower(),
        hashed_password=get_password_hash(admin_in.password),
        role="ADMIN",
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    log_audit(db, "INITIAL_ADMIN_PROVISIONED", admin_user.id, "USER", str(admin_user.id), {"username": admin_user.username}, request)

    access_token = create_access_token(admin_user.id, admin_user.role)
    refresh_token = create_refresh_token(admin_user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserOut.model_validate(admin_user)
    }


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit by IP and by username to prevent brute force attacks
    limited, retry_after = auth_rate_limiter.is_rate_limited(f"login_{client_ip}_{login_data.username}")
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts. Please retry after {retry_after} seconds."
        )

    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to multiple failed login attempts. Try again later.",
        )
        
    if not verify_password(login_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            log_audit(db, "ACCOUNT_LOCKED", user.id, "USER", str(user.id), {"reason": "Max failed attempts exceeded"}, request)
        db.commit()
        log_audit(db, "LOGIN_FAILED", user.id, "USER", str(user.id), {"username": login_data.username}, request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
        
    # Reset failed attempts and rate limiter on success
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    auth_rate_limiter.reset(f"login_{client_ip}_{login_data.username}")
    
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    
    log_audit(db, "LOGIN_SUCCESS", user.id, "USER", str(user.id), {"role": user.role}, request)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user)
    }


@router.post("/refresh")
def refresh_token_endpoint(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    old_jti = payload.get("jti")
    if old_jti:
        # Check if already revoked
        already_revoked = db.query(RevokedToken).filter(RevokedToken.jti == old_jti).first()
        if already_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or already rotated",
            )
        
        # Enforce refresh token rotation by revoking the old refresh token
        exp = datetime.fromtimestamp(payload.get("exp", time.time() + 86400 * 7), tz=timezone.utc)
        db.add(RevokedToken(
            jti=old_jti,
            token_type="refresh",
            expires_at=exp
        ))
        
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active",
        )
        
    new_access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id)
    db.commit()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Extract authorization token and revoke it
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if payload and payload.get("jti"):
            exp_ts = payload.get("exp", time.time() + 3600)
            db.add(RevokedToken(
                jti=payload["jti"],
                token_type=payload.get("type", "access"),
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc)
            ))
            db.commit()

    log_audit(db, "LOGOUT", current_user.id, "USER", str(current_user.id), None, request)
    return {"message": "Logged out and token successfully revoked"}


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    return db.query(User).order_by(User.id.asc()).all()


@router.post("/users", response_model=UserOut)
def create_new_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    existing = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # Validate password strength for new users
    is_strong, reason = validate_password_strength(user_in.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insecure password: {reason}"
        )

    # Validate role
    role = user_in.role.upper()
    if role not in ["ADMIN", "ANALYST", "VIEWER"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: ADMIN, ANALYST, VIEWER"
        )
        
    new_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        hashed_password=get_password_hash(user_in.password),
        role=role,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit(db, "USER_CREATED", current_user.id, "USER", str(new_user.id), {"username": new_user.username, "role": new_user.role}, request)
    return new_user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_update.email is not None:
        user.email = user_update.email.strip().lower()
    if user_update.role is not None:
        role = user_update.role.upper()
        if role not in ["ADMIN", "ANALYST", "VIEWER"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.password:
        is_strong, reason = validate_password_strength(user_update.password)
        if not is_strong:
            raise HTTPException(status_code=400, detail=f"Insecure password: {reason}")
        user.hashed_password = get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(user)
    log_audit(db, "USER_UPDATED", current_user.id, "USER", str(user.id), {"updated_fields": user_update.model_dump(exclude_unset=True)}, request)
    return user
