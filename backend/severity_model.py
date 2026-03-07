"""Severity scoring utilities for incident text."""

from __future__ import annotations

import re
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

_DEESCALATION_WEIGHTS = {
    "good weather": 0.2,
    "clear weather": 0.15,
    "normal operations": 0.2,
    "service restored": 0.2,
    "resolved": 0.15,
    "stable": 0.1,
}

_NEGATION_PREFIX = r"(?:no|not|without|none|never|lack of)"


def score_severity(text: str) -> Tuple[float, str]:
    """Return a severity score (0-1) and categorical label."""
    normalized = text.lower()

    score = 0.2
    for _, terms in _SEVERITY_WEIGHTS.items():
        score += _sum_term_weights(normalized, terms.items())

    # Lower score when text indicates normal conditions or resolved state.
    score -= _sum_term_weights(normalized, _DEESCALATION_WEIGHTS.items(), subtractive=True)

    score = max(0.0, min(score, 1.0))
    label = _label_from_score(score)
    return round(score, 2), label


def _sum_term_weights(text: str, term_weights: Iterable[tuple[str, float]], subtractive: bool = False) -> float:
    """Sum term weights while skipping negated severity phrases."""
    total = 0.0
    for term, weight in term_weights:
        if term in text:
            if not subtractive and _is_negated(text, term):
                continue
            total += weight
    return total


def _is_negated(text: str, term: str) -> bool:
    """Check if a term is directly negated in a short left context window."""
    pattern = rf"\b{_NEGATION_PREFIX}\s+(?:\w+\s+){{0,2}}{re.escape(term)}\b"
    return re.search(pattern, text) is not None


def _label_from_score(score: float) -> str:
    """Map score to a human-readable severity label."""
    if score >= 0.9:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"
