"""Region extraction for incident text using simple regex and dictionaries."""

from __future__ import annotations

import re


_US_REGIONS = [
    "North Texas",
    "South Texas",
    "West Texas",
    "East Texas",
    "Texas",
    "California",
    "Florida",
    "New York",
    "Arizona",
    "Nevada",
]

_COUNTY_PATTERN = re.compile(r"\b([A-Z][a-z]+\sCounty)\b")
_STATE_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")


def extract_region(text: str) -> tuple[str, float]:
    """Extract region name and confidence from free-form incident text."""
    county_match = _COUNTY_PATTERN.search(text)
    if county_match:
        return county_match.group(1), 0.9

    for region in _US_REGIONS:
        if region.lower() in text.lower():
            return region, 0.88

    # Fallback: capture title-cased location-like chunk after "in".
    in_match = re.search(r"\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", text)
    if in_match:
        return in_match.group(1), 0.7

    generic = _STATE_PATTERN.search(text)
    if generic:
        return generic.group(1), 0.5

    return "unknown", 0.3
