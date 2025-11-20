from __future__ import annotations

import csv
from datetime import datetime
from typing import List, Optional

from .models import Event


def _parse_dt(value: str) -> datetime:
    """
    Parse a datetime string in the format 'YYYY-MM-DD HH:MM'.
    """
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")


def load_health_events(csv_path: str) -> List[Event]:
    """
    Load richer health events (heart rate, steps, stress, sleep) from a CSV file.

    Expected CSV columns:
        timestamp_start, timestamp_end, kind, heart_rate_avg,
        steps, stress_level, sleep_hours, notes
    """
    events: List[Event] = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            ts_start = _parse_dt(row["timestamp_start"])
            ts_end_raw = row.get("timestamp_end", "").strip()
            ts_end = _parse_dt(ts_end_raw) if ts_end_raw else ts_start

            kind = (row.get("kind") or "").strip()

            # Optional numeric fields
            hr_raw = (row.get("heart_rate_avg") or "").strip()
            steps_raw = (row.get("steps") or "").strip()
            sleep_raw = (row.get("sleep_hours") or "").strip()
            stress = (row.get("stress_level") or "").strip() or None

            heart_rate_avg: Optional[int] = int(hr_raw) if hr_raw else None
            steps: Optional[int] = int(steps_raw) if steps_raw else None
            sleep_hours: Optional[float] = float(sleep_raw) if sleep_raw else None

            notes = (row.get("notes") or "").strip()

            # Build a friendly title that the AI can understand easily
            title_parts = []

            if kind == "morning_check":
                title_parts.append("Morning health check")
            elif kind == "walk_exercise":
                title_parts.append("Walk / light exercise")
            elif kind == "rest_period":
                title_parts.append("Afternoon rest")
            elif kind == "night_sleep":
                title_parts.append("Night sleep")
            else:
                title_parts.append("Health event")

            if heart_rate_avg is not None:
                title_parts.append(f"HR ~{heart_rate_avg} bpm")

            if steps is not None:
                title_parts.append(f"{steps} steps")

            if sleep_hours is not None:
                title_parts.append(f"{sleep_hours}h sleep")

            if stress:
                title_parts.append(f"stress {stress}")

            title = " | ".join(title_parts)

            details = {
                "kind": kind,
                "heart_rate_avg": heart_rate_avg,
                "steps": steps,
                "stress_level": stress,
                "sleep_hours": sleep_hours,
                "notes": notes,
            }

            event = Event(
                id=f"health-{idx}",
                timestamp_start=ts_start,
                timestamp_end=ts_end,
                source_type="health",
                title=title,
                details=details,
                people=[],      # could add "Patient" / "Caregiver" later if needed
                location=None,
            )
            events.append(event)

    return events

