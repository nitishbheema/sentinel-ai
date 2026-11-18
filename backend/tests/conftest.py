import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.session import SessionLocal, Base, engine
from app.models.models import User
from app.core.security import get_password_hash


@pytest.fixture(scope="session")
def client():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "test_admin").first()
    if not admin:
        admin = User(
            username="test_admin",
            email="test_admin@sentinelai.local",
            hashed_password=get_password_hash("AdminPass123!"),
            role="ADMIN",
            is_active=True
        )
        db.add(admin)
        db.commit()
    db.close()

    res = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "AdminPass123!"
    })
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def analyst_token(client):
    db = SessionLocal()
    analyst = db.query(User).filter(User.username == "test_analyst").first()
    if not analyst:
        analyst = User(
            username="test_analyst",
            email="test_analyst@sentinelai.local",
            hashed_password=get_password_hash("AnalystPass123!"),
            role="ANALYST",
            is_active=True
        )
        db.add(analyst)
        db.commit()
    db.close()

    res = client.post("/api/v1/auth/login", json={
        "username": "test_analyst",
        "password": "AnalystPass123!"
    })
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def viewer_token(client):
    db = SessionLocal()
    viewer = db.query(User).filter(User.username == "test_viewer").first()
    if not viewer:
        viewer = User(
            username="test_viewer",
            email="test_viewer@sentinelai.local",
            hashed_password=get_password_hash("ViewerPass123!"),
            role="VIEWER",
            is_active=True
        )
        db.add(viewer)
        db.commit()
    db.close()

    res = client.post("/api/v1/auth/login", json={
        "username": "test_viewer",
        "password": "ViewerPass123!"
    })
    return res.json()["access_token"]
