"""Severity scoring utilities for incident text."""

from __future__ import annotations

from typing import Iterable, Tuple


_SEVERITY_WEIGHTS = {
    "critical": {
        "widespread": 0.3,
        "emergency": 0.35,
        "catastrophic": 0.35,
        "grid collapse": 0.4,
        "statewide": 0.25,
    },
    "high": {
        "failure": 0.25,
        "collapse": 0.3,
        "major": 0.2,
        "severe": 0.2,
        "instability": 0.2,
    },
    "medium": {
        "outage": 0.2,
        "disruption": 0.2,
        "fluctuation": 0.15,
        "interruption": 0.2,
        "warning": 0.1,
    },
    "low": {
        "minor": 0.1,
        "brief": 0.05,
        "localized": 0.1,
        "contained": 0.1,
    },
}


def score_severity(text: str) -> Tuple[float, str]:
    """Return a severity score (0-1) and categorical label."""
    normalized = text.lower()

    score = 0.2
    for _, terms in _SEVERITY_WEIGHTS.items():
        score += _sum_term_weights(normalized, terms.items())

    score = max(0.0, min(score, 1.0))
    label = _label_from_score(score)
    return round(score, 2), label


def _sum_term_weights(text: str, term_weights: Iterable[tuple[str, float]]) -> float:
    """Add weight for each matching severity term."""
    return sum(weight for term, weight in term_weights if term in text)


def _label_from_score(score: float) -> str:
    """Map score to a human-readable severity label."""
    if score >= 0.9:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"
