from datetime import datetime
from typing import List
from models import Event

def load_photo_events(csv_path: str) -> List[Event]:
    events: List[Event] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        header = True
        for line in f:
            if header:
                header = False
                continue

            photo_id, ts, location, people_str = line.strip().split(",", 3)

            timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M")
            people = [p for p in people_str.split(";") if p.strip()] if people_str else []

            event = Event(
                id=photo_id,
                timestamp_start=timestamp,
                timestamp_end=timestamp,
                source_type="photo",
                title="Photo Taken",
                details={"people_detected": people},
                people=people,
                location=location if location else None
            )
            events.append(event)

    return events

