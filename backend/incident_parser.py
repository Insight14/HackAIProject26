"""Orchestrates incident text parsing into structured signals."""

from __future__ import annotations

from dataclasses import dataclass

from backend.event_classifier import classify_event_type
from backend.region_extractor import extract_region
from backend.severity_model import score_severity


_CAUSE_KEYWORDS = {
    "storm": ["storm", "thunderstorm", "hurricane", "tornado", "severe weather"],
    "heatwave": ["heatwave", "extreme heat", "high temperature"],
    "wildfire": ["wildfire", "brush fire", "forest fire"],
    "equipment failure": ["equipment", "transformer", "relay", "breaker", "mechanical fault"],
    "cyber attack": ["cyber", "malware", "ransomware", "intrusion", "ddos"],
}


@dataclass
class IncidentSignal:
    event_type: str
    cause: str
    severity: str
    severity_score: float
    region: str
    confidence: float


def parse_incident_text(text: str) -> IncidentSignal:
    """Parse raw incident report text into a structured signal."""
    event_type, event_conf = classify_event_type(text)
    cause, cause_conf = _detect_cause(text)
    severity_score, severity_label = score_severity(text)
    region, region_conf = extract_region(text)

    # Blend component confidences and mildly reward stronger severity evidence.
    confidence = (event_conf * 0.35) + (cause_conf * 0.25) + (region_conf * 0.2) + (min(severity_score + 0.1, 1.0) * 0.2)

    return IncidentSignal(
        event_type=event_type,
        cause=cause,
        severity=severity_label,
        severity_score=severity_score,
        region=region,
        confidence=round(min(max(confidence, 0.0), 0.99), 2),
    )


def _detect_cause(text: str) -> tuple[str, float]:
    """Infer likely incident cause from text keywords."""
    normalized = text.lower()

    best_cause = "unknown"
    best_hits = 0

    for cause, keywords in _CAUSE_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in normalized)
        if hits > best_hits:
            best_hits = hits
            best_cause = cause

    if best_hits == 0:
        return best_cause, 0.35

    confidence = min(0.6 + (0.1 * best_hits), 0.95)
    return best_cause, round(confidence, 2)
