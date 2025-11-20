from __future__ import annotations

import argparse
from datetime import date

from ingest_calendar import load_calendar_events
from ingest_locations import load_location_events
from ingest_messages import load_message_events
from ingest_photos import load_photo_events
from ingest_health import load_health_events
from ingest_calls import load_call_events
from ingest_gps import load_gps_events
from ingest_whatsapp import load_whatsapp_events

from timeline import (
    group_into_sessions,
    summarize_session,
    filter_events_for_day,
)
from story_generator import generate_ai_story_with_ollama



# ---------------------------------------------------------------------
# Shared helper: parse CLI date
# ---------------------------------------------------------------------
def _parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD into a date, or exit with a friendly message."""
    try:
        y, m, d = map(int, date_str.split("-"))
        return date(y, m, d)
    except Exception as exc:
        raise SystemExit(
            f"Invalid --date value {date_str!r}. Expected YYYY-MM-DD."
        ) from exc


# ---------------------------------------------------------------------
# NEW: wrapper that Streamlit (or any UI) can call directly
# ---------------------------------------------------------------------
def run_engine_for_date(
    target_date: date,
    data_dir: str = "data",
    gap_minutes: int = 60,
) -> dict:
    """
    Run the whole pipeline for a given date and return structured results.

    This is UI-friendly: no argparse, no printing; just inputs -> dict.
    Streamlit will import and call this function.
    """
    data_dir = data_dir.rstrip("/\\")  # avoid accidental double slashes

    # Load events from all sources
    calendar_events = load_calendar_events(f"{data_dir}/calendar_events_sample.csv")
    location_events = load_location_events(f"{data_dir}/locations_sample.csv")
    message_events = load_message_events(f"{data_dir}/messages_sample.csv")
    photo_events = load_photo_events(f"{data_dir}/photos_sample.csv")
    health_events = load_health_events(f"{data_dir}/health_sample.csv")
    call_events = load_call_events(f"{data_dir}/calls_sample.csv")
    gps_events = load_gps_events(f"{data_dir}/gps_sample.csv")
    whatsapp_events = load_whatsapp_events(f"{data_dir}/whatsapp_sample.csv")

    events_by_source = {
        "Calendar": calendar_events,
        "Location": location_events,
        "Messages": message_events,
        "Photos": photo_events,
        "Health": health_events,
        "Calls": call_events,
        "GPS": gps_events,
        "WhatsApp": whatsapp_events,
    }

    # Flatten and filter to the target day
    all_events = [ev for events in events_by_source.values() for ev in events]
    day_events = filter_events_for_day(all_events, target_date)

    if not day_events:
        # Still return a dict so UI can show a friendly message
        return {
            "target_date": target_date,
            "total_events": 0,
            "num_sessions": 0,
            "memory_story": (
                f"No events were found for {target_date.isoformat()}. "
                "There is nothing to reconstruct for this day."
            ),
            "caregiver_summary": (
                "- No specific activities were recorded for this date.\n"
                "- Continue gentle check-ins according to the usual routine."
            ),
            "per_source_counts": {k: len(v) for k, v in events_by_source.items()},
        }

    # Build sessions + summaries
    sessions = group_into_sessions(day_events, gap_minutes=gap_minutes)
    summaries = [summarize_session(s) for s in sessions]

    # AI-generated narrative + caregiver summary (safe, deterministic)
    result = generate_ai_story_with_ollama(summaries, target_date.isoformat())

    return {
        "target_date": target_date,
        "total_events": len(day_events),
        "num_sessions": len(sessions),
        "memory_story": result["memory_story"],
        "caregiver_summary": result["caregiver_summary"],
        "per_source_counts": {k: len(v) for k, v in events_by_source.items()},
    }


# ---------------------------------------------------------------------
# Existing CLI entry point (kept as-is for terminal usage)
# ---------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI Memory Archaeology Engine")
    parser.add_argument(
        "--date",
        default="2025-01-01",
        help="Target date in YYYY-MM-DD format (default: 2025-01-01)",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing *_sample.csv files (default: data)",
    )
    parser.add_argument(
        "--gap-minutes",
        type=int,
        default=60,
        help="Gap in minutes used to split sessions (default: 60)",
    )

    args = parser.parse_args(argv)
    target_date = _parse_date(args.date)
    data_dir = args.data_dir.rstrip("/\\")  # avoid accidental double slashes

    print(f"Loading events for {target_date} from '{data_dir}'...\n")

    # Load events from all sources
    calendar_events = load_calendar_events(f"{data_dir}/calendar_events_sample.csv")
    location_events = load_location_events(f"{data_dir}/locations_sample.csv")
    message_events = load_message_events(f"{data_dir}/messages_sample.csv")
    photo_events = load_photo_events(f"{data_dir}/photos_sample.csv")
    health_events = load_health_events(f"{data_dir}/health_sample.csv")
    call_events = load_call_events(f"{data_dir}/calls_sample.csv")
    gps_events = load_gps_events(f"{data_dir}/gps_sample.csv")
    whatsapp_events = load_whatsapp_events(f"{data_dir}/whatsapp_sample.csv")

    events_by_source = {
        "Calendar": calendar_events,
        "Location": location_events,
        "Messages": message_events,
        "Photos": photo_events,
        "Health": health_events,
        "Calls": call_events,
        "GPS": gps_events,
        "WhatsApp": whatsapp_events,
    }

    # Per-source counts
    total_events = 0
    for source_name, events in events_by_source.items():
        count = len(events)
        print(f"{source_name} events: {count}")
        total_events += count

    print(f"\nTotal events loaded (all days): {total_events}")

    # Filter to the target day
    all_events = [ev for events in events_by_source.values() for ev in events]
    day_events = filter_events_for_day(all_events, target_date)
    print(f"Total events on {target_date}: {len(day_events)}")

    if not day_events:
        print("\nNo events found for this date. Nothing to send to the story generator.")
        return

    # Build sessions
    sessions = group_into_sessions(day_events, gap_minutes=args.gap_minutes)
    print(f"Number of sessions: {len(sessions)}\n")

    # Summaries for the model
    summaries = [summarize_session(s) for s in sessions]

    # AI-generated narrative + caregiver summary
    result = generate_ai_story_with_ollama(summaries, str(target_date))

    print("\n=== MEMORY STORY (AI) ===\n")
    print(result["memory_story"])

    print("\n=== CAREGIVER SUMMARY (AI) ===\n")
    print(result["caregiver_summary"])


if __name__ == "__main__":
    main()

