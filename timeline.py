from datetime import date, timedelta
from typing import List, Dict, Any
from models import Event

def filter_events_for_day(events: List[Event], target_date: date) -> List[Event]:
    """
    Return events whose start timestamp falls on the target_date,
    sorted by time.
    """
    same_day_events = [
        e for e in events
        if e.timestamp_start.date() == target_date
    ]

    return sorted(same_day_events, key=lambda e: e.timestamp_start)

def group_into_sessions(events: List[Event], gap_minutes: int = 60) -> List[List[Event]]:
    """
    Group events into 'sessions' if the gap between consecutive events
    is less than or equal to gap_minutes.
    """
    if not events:
        return []

    sessions: List[List[Event]] = []
    current_session: List[Event] = [events[0]]

    for prev, curr in zip(events, events[1:]):
        gap = curr.timestamp_start - prev.timestamp_start
        if gap <= timedelta(minutes=gap_minutes):
            # same session
            current_session.append(curr)
        else:
            # start a new session
            sessions.append(current_session)
            current_session = [curr]

    sessions.append(current_session)
    return sessions

def summarize_session(session: List[Event]) -> Dict[str, Any]:
    """
    Turn a list of Events into a compact session summary dictionary.
    """
    start = session[0].timestamp_start
    end = session[-1].timestamp_end or session[-1].timestamp_start

    locations = {e.location for e in session if e.location}
    people = set()
    for e in session:
        for p in e.people:
            people.add(p)

    titles = [e.title for e in session if e.title]

    summary = {
        "start": start,
        "end": end,
        "locations": list(locations),
        "people": list(people),
        "titles": titles,
        "raw_events": session,  # we keep the original events too
    }

    return summary

