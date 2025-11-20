import csv
from datetime import datetime
from typing import List

from models import Event


def load_gps_events(csv_path: str) -> List[Event]:
    """
    Load GPS / location-visit events from a CSV file and convert them into Event objects.

    Expected CSV columns:
    id,timestamp_start,timestamp_end,place_name,lat,lon,source
    """

    events: List[Event] = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamps like "2025-01-01 08:30"
            start = datetime.strptime(row["timestamp_start"], "%Y-%m-%d %H:%M")
            end = datetime.strptime(row["timestamp_end"], "%Y-%m-%d %H:%M")

            place_name = row.get("place_name", "").strip()
            lat = row.get("lat", "").strip()
            lon = row.get("lon", "").strip()
            source = row.get("source", "gps").strip()

            # Title that will show up in summaries / AI prompt
            if place_name:
                title = f"Visit at {place_name} (GPS)"
            else:
                title = "GPS location visit"

            details = {
                "lat": lat,
                "lon": lon,
                "source": source,
                "raw_place_name": place_name,
            }

            ev = Event(
                id=row["id"],
                timestamp_start=start,
                timestamp_end=end,
                source_type="gps",   # distinguish from 'calendar' / 'location'
                title=title,
                details=details,
                people=[],           # GPS alone doesn’t know who was there
                location=place_name if place_name else None,
            )

            events.append(ev)

    return events

