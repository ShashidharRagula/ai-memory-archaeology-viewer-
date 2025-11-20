from datetime import datetime
from typing import List
from .models import Event

def load_message_events(csv_path: str) -> List[Event]:
    events: List[Event] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = True
    for line in lines:
        if header:
            header = False
            continue

        msg_id, ts, person, msg_type, preview = line.strip().split(",", 4)

        timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M")

        event = Event(
            id=msg_id,
            timestamp_start=timestamp,
            timestamp_end=timestamp,
            source_type="message",
            title=f"Message with {person}",
            details={"message_type": msg_type, "preview": preview},
            people=[person],
            location=None
        )
        events.append(event)

    return events
