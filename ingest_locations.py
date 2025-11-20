import csv
from datetime import datetime
from typing import List
from models import Event

def load_location_events(csv_path: str) -> List[Event]:
    events: List[Event] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = datetime.strptime(row["timestamp_start"], "%Y-%m-%d %H:%M")
            end = datetime.strptime(row["timestamp_end"], "%Y-%m-%d %H:%M")

            place = row["place_name"]

            event = Event(
                id=row["location_id"],
                timestamp_start=start,
                timestamp_end=end,
                source_type="location",
                title=f"At {place}",
                details={"place_name": place},
                people=[],          # location events usually have no explicit people
                location=place
            )
            events.append(event)

    return events

