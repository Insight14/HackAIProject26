"""Fetch and normalize natural disaster events from public APIs."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import requests

NOAA_API_URL = "https://api.weather.gov/alerts/active"
NASA_FIRMS_CSV_URL = (
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/"
    "MODIS_C6_USA_contiguous_and_Hawaii_24h.csv"
)


def fetch_noaa_alerts() -> list[dict[str, Any]]:
    """Fetch and normalize active alerts from NOAA Weather API."""
    events: list[dict[str, Any]] = []
    try:
        resp = requests.get(
            NOAA_API_URL,
            headers={"User-Agent": "GridWatch/1.0 (natural-disaster-ingest)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            events.append(
                {
                    "event_type": props.get("event", "Unknown"),
                    "region": props.get("areaDesc", "Unknown"),
                    "timestamp": props.get("sent", ""),
                    "severity": (props.get("severity", "") or "").lower() or "medium",
                    "source": "NOAA",
                    "description": props.get("description", ""),
                }
            )
    except Exception as exc:  # noqa: BLE001
        print(f"NOAA API error: {exc}")
    return events


def _brightness_to_severity(brightness: float) -> str:
    if brightness < 330:
        return "low"
    if brightness < 370:
        return "medium"
    return "high"


def _normalize_acq_time(raw_time: str) -> str:
    """Normalize FIRMS HHMM time into HH:MM for an ISO-like timestamp."""
    digits = (raw_time or "").strip().zfill(4)
    if len(digits) != 4 or not digits.isdigit():
        return "00:00"
    return f"{digits[:2]}:{digits[2:]}"


def fetch_nasa_firms_wildfires() -> list[dict[str, Any]]:
    """Fetch and normalize wildfire detections from NASA FIRMS CSV endpoint."""
    events: list[dict[str, Any]] = []
    try:
        resp = requests.get(NASA_FIRMS_CSV_URL, timeout=10)
        resp.raise_for_status()

        reader = csv.DictReader(StringIO(resp.text))
        for row in reader:
            try:
                brightness = float(row.get("brightness", 0))
                acq_date = row.get("acq_date", "")
                acq_time = _normalize_acq_time(row.get("acq_time", ""))
                events.append(
                    {
                        "event_type": "Wildfire",
                        "region": f"{row.get('latitude', '')},{row.get('longitude', '')}",
                        "timestamp": f"{acq_date}T{acq_time}:00Z" if acq_date else "",
                        "severity": _brightness_to_severity(brightness),
                        "source": "NASA FIRMS",
                        "description": (
                            f"Brightness: {brightness}, Confidence: {row.get('confidence', '')}, "
                            f"FRP: {row.get('frp', '')}"
                        ),
                    }
                )
            except Exception as row_exc:  # noqa: BLE001
                print(f"FIRMS row parse error: {row_exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"NASA FIRMS API error: {exc}")
    return events


def get_active_disaster_events() -> list[dict[str, Any]]:
    """Return normalized disaster events from all configured sources."""
    return [*fetch_noaa_alerts(), *fetch_nasa_firms_wildfires()]
