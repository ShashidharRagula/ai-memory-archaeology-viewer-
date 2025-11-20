import csv
from datetime import datetime
from typing import List

from .models import Event


def load_call_events(csv_path: str) -> List[Event]:
    """
    Load phone call events from a CSV file and convert them into Event objects.

    Expected CSV columns:
    id,timestamp_start,timestamp_end,person,direction,duration_min
    """

    events: List[Event] = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamps
            start = datetime.strptime(row["timestamp_start"], "%Y-%m-%d %H:%M")
            end = datetime.strptime(row["timestamp_end"], "%Y-%m-%d %H:%M")

            person = row.get("person", "").strip()
            direction = row.get("direction", "").strip().lower()
            duration_min = row.get("duration_min", "").strip()

            # Build the title for this event
            if person:
                if direction == "incoming":
                    title = f"Phone call from {person}"
                elif direction == "outgoing":
                    title = f"Phone call to {person}"
                else:
                    title = f"Phone call with {person}"
            else:
                title = "Phone call"

            # Details dictionary can hold extra info
            details = {
                "direction": direction,
                "duration_min": duration_min,
                "raw_person": person,
            }

            # People list: who was involved in the call
            people = [person] if person else []

            ev = Event(
                id=row["id"],
                timestamp_start=start,
                timestamp_end=end,
                source_type="call",
                title=title,
                details=details,
                people=people,
                location=None,  # We don't know location for calls
            )

            events.append(ev)

    return events
