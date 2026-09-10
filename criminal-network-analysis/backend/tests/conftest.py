"""Shared pytest fixtures: an isolated in-memory SQLite database seeded with
the same synthetic dataset generator used for local development, and a
FastAPI TestClient wired to that database instead of the real dev DB file."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.alert import Alert
from app.models.case import Case
from app.models.entities import Person, Organization, Vehicle, Phone, Location, Account
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User
from app.security.auth import hash_password
from app.analytics.anomaly_detection import run_all_rules
from seed.generate_synthetic_data import generate


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def seeded_database(TestSessionLocal):
    """Seed the in-memory database once for the whole test session."""
    db = TestSessionLocal()
    data = generate()

    for u in data["users"]:
        db.add(User(id=u["id"], username=u["username"], full_name=u["full_name"], email=u["email"],
                     hashed_password=hash_password(u["password"]), role=u["role"], is_active=True))
    for c in data["cases"]:
        db.add(Case(**c))
    for p in data["persons"]:
        db.add(Person(**p))
    for o in data["organizations"]:
        db.add(Organization(**o))
    for v in data["vehicles"]:
        db.add(Vehicle(**v))
    for ph in data["phones"]:
        db.add(Phone(**ph))
    for loc in data["locations"]:
        db.add(Location(**loc))
    for a in data["accounts"]:
        db.add(Account(**a))
    for r in data["relationships"]:
        db.add(Relationship(**r))
    for e in data["events"]:
        db.add(Event(**e))
    for ev in data["evidence"]:
        db.add(Evidence(**ev))
    db.commit()

    from datetime import datetime, timezone
    drafts = run_all_rules(db)
    for i, draft in enumerate(drafts, start=1):
        db.add(Alert(id=f"ALERT-{i:04d}", timestamp=datetime.now(timezone.utc), **draft))
    db.commit()
    db.close()
    yield data


@pytest.fixture()
def client(TestSessionLocal):
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def investigator_token(client):
    response = client.post("/api/auth/login", json={"username": "investigator.demo", "password": "InvestigatorDemo@123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def analyst_token(client):
    response = client.post("/api/auth/login", json={"username": "analyst.demo", "password": "AnalystDemo@123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(investigator_token):
    return {"Authorization": f"Bearer {investigator_token}"}
