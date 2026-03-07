"""Risk scoring logic based on structured incident signals."""

from __future__ import annotations

from dataclasses import dataclass


_EVENT_WEIGHTS = {
    "power outage": 0.55,
    "transmission failure": 0.8,
    "grid overload": 0.9,
    "storm damage": 0.75,
    "wildfire risk": 0.9,
    "equipment failure": 0.7,
    "unknown": 0.45,
}

_CAUSE_MULTIPLIERS = {
    "storm": 1.05,
    "heatwave": 1.08,
    "wildfire": 1.2,
    "equipment failure": 1.0,
    "cyber attack": 1.25,
    "unknown": 0.95,
}


@dataclass
class RiskAssessment:
    risk_score: float
    risk_level: str
    recommended_action: str


def score_incident_risk(
    *,
    event_type: str,
    cause: str,
    severity_score: float,
    confidence: float,
) -> RiskAssessment:
    """Compute a normalized risk score and recommendation."""
    event_norm = _EVENT_WEIGHTS.get(event_type, _EVENT_WEIGHTS["unknown"])
    cause_mult = _CAUSE_MULTIPLIERS.get(cause, _CAUSE_MULTIPLIERS["unknown"])

    # Weighted base before cause multiplier.
    base = (
        (severity_score * 0.5)
        + (event_norm * 0.25)
        + ((1.0 if cause != "unknown" else 0.45) * 0.15)
        + (confidence * 0.1)
    )

    risk_score = max(0.0, min(base * cause_mult, 1.0))
    risk_level = _risk_level(risk_score)
    recommended_action = _recommended_action(risk_level)

    return RiskAssessment(
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        recommended_action=recommended_action,
    )


def _risk_level(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.7:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _recommended_action(risk_level: str) -> str:
    if risk_level == "critical":
        return "immediate escalation, dispatch field crew, and issue public alert"
    if risk_level == "high":
        return "dispatch operations team and issue regional alert"
    if risk_level == "medium":
        return "increase monitoring and prepare standby response"
    return "log incident and continue routine monitoring"
