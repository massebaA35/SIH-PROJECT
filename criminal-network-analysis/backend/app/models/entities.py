"""
Entity tables. Every entity across every table shares a globally-unique,
type-prefixed id (PERSON-101, ORG-201, VEHICLE-301, PHONE-401, LOC-501,
ACCOUNT-601) so relationships/events/graph code can reference any entity
without knowing which table it lives in.
"""
from datetime import date

from sqlalchemy import String, Date, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    gender: Mapped[str] = mapped_column(String(16), default="")
    age_range: Mapped[str] = mapped_column(String(16), default="")
    nationality: Mapped[str] = mapped_column(String(64), default="India (synthetic)")
    occupation: Mapped[str] = mapped_column(String(128), default="")
    region: Mapped[str] = mapped_column(String(64), default="")
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    org_type: Mapped[str] = mapped_column(String(64), default="")
    region: Mapped[str] = mapped_column(String(64), default="")
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    registration: Mapped[str] = mapped_column(String(32))  # synthetic plate, e.g. KL-07-AB-1234
    vehicle_type: Mapped[str] = mapped_column(String(64), default="")
    color: Mapped[str] = mapped_column(String(32), default="")
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    number: Mapped[str] = mapped_column(String(32))  # synthetic, e.g. XXXXX-90000
    carrier: Mapped[str] = mapped_column(String(64), default="")
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    region: Mapped[str] = mapped_column(String(64), default="")
    location_type: Mapped[str] = mapped_column(String(64), default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")


class Account(Base):
    """Synthetic financial account -- never a real account number."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    masked_number: Mapped[str] = mapped_column(String(32))  # e.g. XXXX-XXXX-4471
    institution: Mapped[str] = mapped_column(String(128), default="")
    account_type: Mapped[str] = mapped_column(String(64), default="")
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")
