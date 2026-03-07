"""Region extraction for incident text using simple regex and dictionaries."""

from __future__ import annotations

import re


_US_REGIONS = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "District of Columbia",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
]

_US_STATE_ABBREVIATIONS = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

_COUNTY_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}\sCounty)\b")
_STATE_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")
_STATE_ABBR_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(_US_STATE_ABBREVIATIONS.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def extract_region(text: str) -> tuple[str, float]:
    """Extract region name and confidence from free-form incident text."""
    county_match = _COUNTY_PATTERN.search(text)
    if county_match:
        return county_match.group(1), 0.9

    for region in _US_REGIONS:
        if region.lower() in text.lower():
            return region, 0.88

    # Handle state abbreviations in natural text (e.g., TX, CA, NY).
    abbr_match = _STATE_ABBR_PATTERN.search(text)
    if abbr_match:
        return _US_STATE_ABBREVIATIONS[abbr_match.group(1).upper()], 0.82

    # Fallback: capture title-cased location-like chunk after "in".
    in_match = re.search(r"\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", text)
    if in_match:
        return in_match.group(1), 0.7

    generic = _STATE_PATTERN.search(text)
    if generic:
        return generic.group(1), 0.5

    return "unknown", 0.3
