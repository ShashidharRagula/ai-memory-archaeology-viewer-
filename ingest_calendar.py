import csv
from datetime import datetime
from typing import List
from models import Event

def load_calendar_events(csv_path: str) -> List[Event]:
    events = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event = Event(
                id=row["event_id"],
                timestamp_start=datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M"),
                timestamp_end=datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M"),
                source_type="calendar",
                title=row["title"],
                details={"raw_location": row["location"]},
                people=[p.strip() for p in row["people"].split(",") if p.strip()],
                location=row["location"]
            )
            events.append(event)

    return events

