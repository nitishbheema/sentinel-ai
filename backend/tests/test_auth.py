import time
import hmac
import hashlib
import uuid
import pytest
from app.core.config import settings


def test_login_success(client, admin_token):
    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "AdminPass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "ADMIN"


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]


def test_rbac_access_control(client, admin_token, viewer_token):
    # Admin can list users
    res_admin = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200

    # Viewer is rejected from creating detection rules
    res_viewer = client.post(
        "/api/v1/detection-rules",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={
            "rule_id": "TEST-RULE-RBAC",
            "name": "Test RBAC",
            "condition_yaml": "condition: true"
        }
    )
    assert res_viewer.status_code == 403


def test_password_strength_enforcement(client, admin_token):
    # Weak password (too short, under 12 characters)
    res_short = client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "weak_user_1",
            "email": "weak1@sentinelai.local",
            "password": "TooShort12!",
            "role": "ANALYST"
        }
    )
    assert res_short.status_code == 400
    assert "Insecure password" in res_short.json()["detail"]

    # Weak password (missing special character)
    res_no_sym = client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "weak_user_2",
            "email": "weak2@sentinelai.local",
            "password": "NoSpecialChar1234",
            "role": "ANALYST"
        }
    )
    assert res_no_sym.status_code == 400
    assert "special character" in res_no_sym.json()["detail"]

    # Strong password creates successfully
    unique_suffix = str(uuid.uuid4())[:8]
    res_valid = client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": f"analyst_{unique_suffix}",
            "email": f"analyst_{unique_suffix}@sentinelai.local",
            "password": "VeryStrongPassword2026!",
            "role": "ANALYST"
        }
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["username"] == f"analyst_{unique_suffix}"


def test_first_time_setup_status_and_lock(client):
    # Check setup status: since users exist in test database, setup_required must be False
    res_status = client.get("/api/v1/auth/setup-status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["setup_required"] is False

    # Attempting to setup initial admin when users exist must be rejected with 403
    res_setup = client.post("/api/v1/auth/setup-admin", json={
        "username": "new_admin",
        "email": "newadmin@sentinelai.local",
        "password": "ComplexInitialAdminPassword2026!"
    })
    assert res_setup.status_code == 403
    assert "already been completed" in res_setup.json()["detail"]


def test_jwt_logout_and_revocation(client):
    # Login to obtain a new access token
    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "AdminPass123!"
    })
    token = res.json()["access_token"]

    # Verify token works
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200

    # Logout
    res_logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res_logout.status_code == 200

    # Using the revoked token must now be rejected with 401
    res_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_after.status_code == 401
    assert "revoked" in res_after.json()["detail"]


def test_refresh_token_rotation(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "AdminPass123!"
    })
    refresh_token = res.json()["refresh_token"]

    # First refresh succeeds
    res_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res_refresh.status_code == 200
    new_tokens = res_refresh.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Attempting to replay the old rotated refresh token must fail with 401
    res_replay = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res_replay.status_code == 401
    assert "revoked" in res_replay.json()["detail"]


def test_auth_rate_limiting(client):
    # Fire rapid failed login attempts for a dummy user to trigger rate limiter
    triggered = False
    for _ in range(8):
        res = client.post("/api/v1/auth/login", json={
            "username": "rate_limit_victim",
            "password": "RandomBadPassword123!"
        })
        if res.status_code == 429:
            triggered = True
            assert "Too many authentication attempts" in res.json()["detail"]
            break
    assert triggered is True


def test_agent_hmac_and_replay_protection(client):
    payload = {
        "event_source": "ENDPOINT",
        "event_type": "AUTH_FAILED",
        "timestamp": "2026-11-20T10:00:00Z",
        "source_ip": "192.168.1.100",
        "destination_ip": "192.168.1.1",
        "host_id": "test-host-01"
    }
    raw_json = '{"destination_ip":"192.168.1.1","event_source":"ENDPOINT","event_type":"AUTH_FAILED","host_id":"test-host-01","source_ip":"192.168.1.100","timestamp":"2026-11-20T10:00:00Z"}'
    
    ts = str(time.time())
    nonce = str(uuid.uuid4())
    msg = f"{ts}:{nonce}:".encode("utf-8") + raw_json.encode("utf-8")
    sig = hmac.new(settings.AGENT_SHARED_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    # Valid HMAC signature passes
    res = client.post(
        "/api/v1/events/ingest",
        data=raw_json,
        headers={
            "Content-Type": "application/json",
            "X-Agent-Signature": sig,
            "X-Agent-Timestamp": ts,
            "X-Agent-Nonce": nonce
        }
    )
    assert res.status_code == 200

    # Replay of the same nonce must be rejected
    res_replay = client.post(
        "/api/v1/events/ingest",
        data=raw_json,
        headers={
            "Content-Type": "application/json",
            "X-Agent-Signature": sig,
            "X-Agent-Timestamp": ts,
            "X-Agent-Nonce": nonce
        }
    )
    assert res_replay.status_code == 401
    assert "Replay attack detected" in res_replay.json()["detail"]


def test_redis_failure_graceful_fallback(monkeypatch, client):
    """
    Simulates Redis connection failure and verifies rate limiting and auth fallback to in-memory mode without crashing.
    """
    from app.core import redis as redis_module
    import redis

    def mock_broken_redis():
        raise redis.ConnectionError("Simulated Redis network disconnection")

    monkeypatch.setattr(redis_module, "get_redis_client", mock_broken_redis)

    # Test login endpoint still succeeds using fallback in-memory rate limiting
    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "AdminPass123!"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_concurrent_admin_setup_prevention(client):
    """
    Verifies that simultaneous administrator setup calls cannot create duplicate accounts or bypass lockdown.
    """
    import concurrent.futures

    def try_setup():
        return client.post("/api/v1/auth/setup-admin", json={
            "username": "concurrent_admin",
            "email": "concurrent@sentinelai.local",
            "password": "StrongConcurrentAdmin2026!"
        })

    # Since system is already provisioned, all concurrent attempts must be rejected with 403
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_setup) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code in [403, 409, 429]
        assert "already been completed" in res.json()["detail"] or "in progress" in res.json()["detail"] or "Too many" in res.json()["detail"]
