"""Rule-based event classification for incident reports."""

from __future__ import annotations

from typing import Iterable, Tuple


_EVENT_KEYWORDS = {
    "transmission failure": [
        "transmission line failure",
        "transmission failure",
        "line failure",
        "substation trip",
        "grid line down",
    ],
    "power outage": [
        "power outage",
        "blackout",
        "brownout",
        "service interruption",
        "no power",
    ],
    "grid overload": [
        "grid overload",
        "load spike",
        "overload",
        "demand surge",
        "over capacity",
    ],
    "storm damage": [
        "storm damage",
        "severe weather",
        "storm activity",
        "thunderstorm",
        "hurricane",
        "tornado",
    ],
    "wildfire risk": [
        "wildfire",
        "brush fire",
        "fire weather",
        "high fire risk",
        "red flag warning",
    ],
    "equipment failure": [
        "equipment failure",
        "transformer failure",
        "relay malfunction",
        "breaker failure",
        "mechanical fault",
        "equipment fault",
    ],
}


def classify_event_type(text: str) -> Tuple[str, float]:
    """Return the most likely event type and a simple confidence score."""
    normalized = text.lower()

    best_event = "unknown"
    best_hits = 0

    for event_type, keywords in _EVENT_KEYWORDS.items():
        hits = _count_hits(normalized, keywords)
        if hits > best_hits:
            best_hits = hits
            best_event = event_type

    if best_hits == 0:
        return best_event, 0.35

    confidence = min(0.6 + (0.1 * best_hits), 0.95)
    return best_event, round(confidence, 2)


def _count_hits(text: str, keywords: Iterable[str]) -> int:
    """Count keyword phrase matches inside the text."""
    return sum(1 for keyword in keywords if keyword in text)
