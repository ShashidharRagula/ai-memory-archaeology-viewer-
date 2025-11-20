from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class Event:
    """
    A single 'thing that happened' in the person's life.

    This could be:
    - a calendar event
    - a location visit
    - a phone call
    - a message
    - a health data point (e.g., heart rate spike)
    """
    id: str                       # unique ID we assign
    timestamp_start: datetime     # when it started
    timestamp_end: Optional[datetime]  # when it ended (can be None)
    source_type: str              # "calendar", "location", "message", etc.
    title: str                    # short label, e.g., "Visited hospital"
    details: Dict                 # raw metadata (original fields from data)
    people: List[str]             # names/labels of people involved
    location: Optional[str] = None  # place name, e.g., "Home", "Clinic"
