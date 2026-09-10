"""
Create all tables and load the synthetic dataset into the database.

Usage (from backend/):
    python -m seed.seed_db
    python -m seed.seed_db --reset      # drop and recreate all tables first
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `app` importable

from datetime import datetime, timezone  # noqa: E402

from app.analytics.anomaly_detection import run_all_rules  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.alert import Alert  # noqa: E402
from app.models.case import Case  # noqa: E402
from app.models.entities import Person, Organization, Vehicle, Phone, Location, Account  # noqa: E402
from app.models.evidence import Evidence  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.relationship import Relationship  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security.auth import hash_password  # noqa: E402
from seed.generate_synthetic_data import generate  # noqa: E402


def seed(reset: bool = False) -> None:
    if reset:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)

    print("Creating tables (if not already present)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(User).count() > 0 and not reset:
            print("Database already contains data. Use --reset to reseed from scratch. Skipping.")
            return

        print("Generating synthetic dataset...")
        data = generate()

        print("Inserting users (passwords hashed with bcrypt)...")
        for u in data["users"]:
            db.add(User(
                id=u["id"], username=u["username"], full_name=u["full_name"], email=u["email"],
                hashed_password=hash_password(u["password"]), role=u["role"], is_active=True,
            ))

        print(f"Inserting {len(data['cases'])} cases...")
        for c in data["cases"]:
            db.add(Case(**c))

        print(f"Inserting {len(data['persons'])} persons, {len(data['organizations'])} organizations, "
              f"{len(data['vehicles'])} vehicles, {len(data['phones'])} phones, "
              f"{len(data['locations'])} locations, {len(data['accounts'])} accounts...")
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

        print(f"Inserting {len(data['relationships'])} relationships...")
        for r in data["relationships"]:
            db.add(Relationship(**r))

        print(f"Inserting {len(data['events'])} events...")
        for e in data["events"]:
            db.add(Event(**e))

        print(f"Inserting {len(data['evidence'])} evidence records...")
        for ev in data["evidence"]:
            db.add(Evidence(**ev))

        db.commit()

        print("Running rule-based anomaly detection to seed initial alerts...")
        drafts = run_all_rules(db)
        for i, draft in enumerate(drafts, start=1):
            db.add(Alert(id=f"ALERT-{i:04d}", timestamp=datetime.now(timezone.utc), **draft))
        db.commit()
        print(f"  -> {len(drafts)} alerts generated from {len(data['relationships'])} relationships / {len(data['events'])} events.")
        print("\nSeed complete.")
        print("\nDemo accounts (prototype only -- never use these in production):")
        for u in data["users"]:
            print(f"  {u['role']:14s} username={u['username']:20s} password={u['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding.")
    args = parser.parse_args()
    seed(reset=args.reset)
