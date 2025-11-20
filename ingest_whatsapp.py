# src/ingest_whatsapp.py

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from typing import List

from .models import Event

# Adjust this if you change the format in the CSV
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def _parse_timestamp(value: str) -> datetime:
    """Parse a timestamp string from the WhatsApp CSV."""
    return datetime.strptime(value.strip(), DATETIME_FORMAT)


def load_whatsapp_events(csv_path: str) -> List[Event]:
    """
    Load WhatsApp-style messages from a CSV and convert them into Event objects.

    Expected CSV columns:
        timestamp        -> "2025-01-01 09:30"
        direction        -> "incoming" or "outgoing"
        contact          -> name of the other person
        message_preview  -> short snippet of the message text
    """
    events: List[Event] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            ts = _parse_timestamp(row["timestamp"])
            # Treat each chat as a short 5-minute event
            ts_end = ts + timedelta(minutes=5)

            contact = (row.get("contact") or "").strip()
            direction = (row.get("direction") or "incoming").strip().lower()
            preview = (row.get("message_preview") or "").strip()

            if direction == "outgoing":
                title = f"WhatsApp message to {contact or 'contact'}"
            else:
                title = f"WhatsApp message from {contact or 'contact'}"

            details = {
                "platform": "whatsapp",
                "direction": direction,
                "contact": contact,
                "message_preview": preview,
            }

            events.append(
                Event(
                    id=f"wa-{i}",
                    timestamp_start=ts,
                    timestamp_end=ts_end,
                    source_type="whatsapp",
                    title=title,
                    details=details,
                    people=[contact] if contact else [],
                    location=None,
                )
            )

    return events
