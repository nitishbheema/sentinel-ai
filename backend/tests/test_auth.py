def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "SentinelAdmin2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "admin",
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
            "rule_id": "TEST-RULE",
            "name": "Test",
            "condition_yaml": "condition: true"
        }
    )
    assert res_viewer.status_code == 403
