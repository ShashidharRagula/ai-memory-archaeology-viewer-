from __future__ import annotations

import re
from .ollama_client import generate_text_with_ollama  # kept for compatibility, not used


# --------------------------------------------------------------------
# Basic sanitization helpers
# --------------------------------------------------------------------

_FORBIDDEN_HEALTH_TERMS = (
    "heart rate",
    "hr",
    "bpm",
    "beats per minute",
    "steps",
    "step count",
    "stress",
)


def _sanitize_text(text: str) -> str:
    """
    Remove or soften sensitive health measurements and clean up residual noise.
    """
    if not text:
        return text

    # Remove explicit "bpm" phrases entirely (e.g., "65 bpm", "~70 bpm")
    text = re.sub(r"\b~?\s*\d+\s*bpm\b", "", text, flags=re.IGNORECASE)

    # Remove things like "2500 steps"
    text = re.sub(r"\b\d+\s*steps\b", "", text, flags=re.IGNORECASE)

    # Remove clauses that start with 'vital signs ...'
    text = re.sub(
        r"vital signs[^\.!?]*[\.!?]?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove any leftover forbidden terms
    lowered = text.lower()
    for term in _FORBIDDEN_HEALTH_TERMS:
        if term in lowered:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub("", text)
            lowered = text.lower()

    # Clean extra spaces caused by removals
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def _time_period(dt) -> str:
    """Rough time-of-day label for a datetime."""
    h = dt.hour
    if h < 12:
        return "in the morning"
    elif h < 17:
        return "in the afternoon"
    return "in the evening"


# --------------------------------------------------------------------
# Deterministic narrative from session summaries
# --------------------------------------------------------------------

def _clean_titles_for_story(raw_titles: list[str]) -> str:
    """
    From a list of raw title strings, remove numeric health info and
    other clinical bits, keep only gentle, human-readable labels.
    """
    # Segments we never want to show on their own
    STOP_WORDS = {"low", "medium", "high", "normal", "~"}

    segments: list[str] = []

    for t in raw_titles or []:
        # First remove bpm / steps / stress / etc.
        t = _sanitize_text(t)

        # Split on common separators so we can drop metric-like chunks
        for seg in re.split(r"[|,;/]", t):
            seg = seg.strip()
            if not seg:
                continue

            low = seg.lower()

            # Drop obvious junk / leftover fragments
            if low in STOP_WORDS:
                continue

            # Drop anything that still looks clinical / measurement-like
            if any(k in low for k in ("bpm", "hr ", "hr~", "stress", "steps")):
                continue

            # Drop segments that still contain digits (likely durations, counts, etc.)
            if re.search(r"\d", seg):
                continue

            # Require at least one letter and length ≥ 3 so we don't keep "~" or "ok"
            if not any(c.isalpha() for c in seg) or len(seg) < 3:
                continue

            segments.append(seg)

    if not segments:
        return ""

    # Deduplicate while preserving order
    unique_segments = []
    for s in segments:
        if s not in unique_segments:
            unique_segments.append(s)

    # Keep at most 3 phrases
    return ", ".join(unique_segments[:3])

def _fallback_narrative(session_summaries: list, target_date_str: str) -> str:
    """
    Generate a simple, safe narrative directly from the session data.

    This uses only:
    - start/end times
    - locations
    - people
    - SAFE activity labels (titles cleaned above)

    No guessing, no health interpretation, no extra places.
    """
    if not session_summaries:
        return (
            f"Only a few small moments were recorded on {target_date_str}, "
            "but it was still your day, shaped by your own rhythm and choices."
        )

    intro = f"On {target_date_str}, a few key moments from your day were recorded."

    moment_sentences: list[str] = []

    for i, s in enumerate(session_summaries, start=1):
        period = _time_period(s["start"])
        start_t = s["start"].strftime("%H:%M")
        end_t = s["end"].strftime("%H:%M")

        locs = ", ".join(s["locations"]) if s["locations"] else ""
        if locs:
            loc_phrase = f" at {locs}"
        else:
            loc_phrase = " in a familiar place"

        people = ", ".join(s["people"]) if s["people"] else ""
        if people:
            people_phrase = f" with {people}"
        else:
            people_phrase = ""

        titles_str = _clean_titles_for_story(s["titles"])
        if titles_str:
            act_phrase = f" while focusing on {titles_str.lower()}"
        else:
            act_phrase = ""

        sentence = (
            f"During one moment {period}, between {start_t} and {end_t}, "
            f"you spent time{loc_phrase}{people_phrase}{act_phrase}."
        )
        moment_sentences.append(sentence)

        # We only need a few moments to give a sense of the day
        if i >= 4:
            break

    body = " ".join(moment_sentences)
    closing = (
        "Even though these notes do not capture every detail, "
        "they still trace a gentle outline of how you moved through your day."
    )

    # Two short paragraphs for readability
    return intro + " " + body + "\n\n" + closing


# --------------------------------------------------------------------
# Rule-based caregiver summary (no LLM)
# --------------------------------------------------------------------


def _rule_based_caregiver_summary(session_summaries: list) -> str:
    """
    Build a factual caregiver summary from the same session data,
    with zero speculation and no model-generated guesses.
    """
    if not session_summaries:
        return (
            "- No specific activities were recorded for this day.\n"
            "- Continue gentle check-ins as usual."
        )

    num_sessions = len(session_summaries)

    all_locations: list[str] = []
    all_people: list[str] = []
    has_health = False
    has_messages = False
    has_calls = False

    for s in session_summaries:
        all_locations.extend(s["locations"])
        all_people.extend(s["people"])

        for title in s["titles"]:
            low = title.lower()
            if any(word in low for word in ("health", "doctor", "clinic", "hospital", "appointment", "check")):
                has_health = True
            if any(word in low for word in ("message", "whatsapp", "text")):
                has_messages = True
            if "call" in low:
                has_calls = True

    # Deduplicate while preserving order a bit
    def _unique(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in items:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    locs_unique = _unique(all_locations)
    people_unique = _unique(all_people)

    bullets: list[str] = []

    bullets.append(f"- There were {num_sessions} recorded activity periods today.")

    if locs_unique:
        bullets.append(
            "- Activities took place at locations such as "
            + ", ".join(locs_unique[:4])
            + "."
        )

    if people_unique:
        bullets.append(
            "- Time was spent with "
            + ", ".join(people_unique[:4])
            + "."
        )

    comms_parts = []
    if has_calls:
        comms_parts.append("phone calls")
    if has_messages:
        comms_parts.append("messages")

    if comms_parts:
        bullets.append(
            "- The log for this day includes "
            + " and ".join(comms_parts)
            + " with others."
        )

    if has_health:
        bullets.append(
            "- Some entries relate to health checks or appointments earlier in the day (without detailed measurements)."
        )

    bullets.append("- Continue gentle check-ins according to the usual routine.")

    # Final sanitization pass (just in case any HR words slipped through)
    bullets = [_sanitize_text(b) for b in bullets]

    return "\n".join(bullets)


# --------------------------------------------------------------------
# Public API used by main_memory_engine.py
# --------------------------------------------------------------------


def generate_ai_story_with_ollama(session_summaries: list, target_date_str: str) -> dict:
    """
    Main entry point.

    For safety and predictability, the MEMORY STORY is generated
    deterministically from session_summaries (no model text used).

    The caregiver summary is also rule-based, using only information
    present in the data (no hallucinated ages, biographies, or health).
    """
    memory_story = _fallback_narrative(session_summaries, target_date_str)
    caregiver_summary = _rule_based_caregiver_summary(session_summaries)

    return {
        "memory_story": memory_story,
        "caregiver_summary": caregiver_summary,
    }


# --------------------------------------------------------------------
# Legacy helper kept for compatibility
# --------------------------------------------------------------------


def split_story_sections(ai_text: str):
    """
    Legacy helper kept for compatibility with older code/tests.
    Not used by the new pipeline.
    """
    return ai_text.strip(), ""

