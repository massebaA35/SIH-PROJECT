"""Descriptive analysis for the supplied crime dataset workbook."""
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_PATH = Path(__file__).resolve().parents[3] / "crime_dataset.xlsx"


@lru_cache(maxsize=1)
def load_crime_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Crime dataset not found: {DATASET_PATH}")
    return pd.read_excel(DATASET_PATH)


def _counts(frame: pd.DataFrame, column: str, limit: int = 10) -> list[dict[str, Any]]:
    counts = frame[column].fillna("Unknown").value_counts().head(limit)
    return [{"label": str(label), "count": int(count)} for label, count in counts.items()]


def crime_analysis() -> dict[str, Any]:
    frame = load_crime_dataset().copy()
    occurrence_time = pd.to_datetime(frame["Time of Occurrence"].astype(str), format="%H:%M:%S", errors="coerce")
    frame["occurrence_hour"] = occurrence_time.dt.hour
    closed = frame["Case Closed"].eq("Yes")
    monthly = frame.groupby(frame["Date of Occurrence"].dt.to_period("M")).size().tail(24)
    return {
        "dataset": DATASET_PATH.name,
        "records": int(len(frame)),
        "date_range": {"start": frame["Date of Occurrence"].min().date().isoformat(), "end": frame["Date of Occurrence"].max().date().isoformat()},
        "closure_rate": round(float(closed.mean() * 100), 2),
        "average_victim_age": round(float(frame["Victim Age"].mean()), 2),
        "average_police_deployed": round(float(frame["Police Deployed"].mean()), 2),
        "missing_weapon_records": int(frame["Weapon Used"].isna().sum()),
        "top_cities": _counts(frame, "City"),
        "crime_descriptions": _counts(frame, "Crime Description"),
        "crime_domains": _counts(frame, "Crime Domain"),
        "victim_genders": _counts(frame, "Victim Gender"),
        "weapons": _counts(frame, "Weapon Used"),
        "hourly_distribution": [{"hour": int(hour), "count": int(count)} for hour, count in frame["occurrence_hour"].value_counts().sort_index().items()],
        "monthly_trend": [{"month": str(month), "count": int(count)} for month, count in monthly.items()],
        "disclaimer": "Descriptive statistics from the supplied workbook; they do not establish causation, guilt, or individual risk.",
    }