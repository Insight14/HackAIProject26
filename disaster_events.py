"""
Module: disaster_events.py
Fetches and normalizes natural disaster events from public APIs for a disaster monitoring system.
"""
import requests
from datetime import datetime
from typing import List, Dict, Any

NOAA_API_URL = "https://api.weather.gov/alerts/active"
NASA_FIRMS_CSV_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/MODIS_C6_USA_contiguous_and_Hawaii_24h.csv"  # Public MODIS 24h active fires

# Unified event schema
# {
#   "event_type": "",
#   "region": "",
#   "timestamp": "",
#   "severity": "",
#   "source": "",
#   "description": ""
# }

def fetch_noaa_alerts() -> List[Dict[str, Any]]:
    """Fetch and normalize active alerts from NOAA Weather API."""
    events = []
    try:
        resp = requests.get(NOAA_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            event = {
                "event_type": props.get("event", ""),
                "region": props.get("areaDesc", ""),
                "timestamp": props.get("sent", ""),
                "severity": props.get("severity", ""),
                "source": "NOAA",
                "description": props.get("description", "")
            }
            events.append(event)
    except Exception as e:
        print(f"NOAA API error: {e}")
    return events

def brightness_to_severity(brightness: float) -> str:
    if brightness < 330:
        return "low"
    elif brightness < 370:
        return "medium"
    else:
        return "high"

import csv
from io import StringIO

def fetch_nasa_firms_wildfires() -> List[Dict[str, Any]]:
    """Fetch and normalize wildfire detections from NASA FIRMS public CSV endpoint."""
    events = []
    try:
        resp = requests.get(NASA_FIRMS_CSV_URL, timeout=10)
        resp.raise_for_status()
        csvfile = StringIO(resp.text)
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Required fields: latitude, longitude, acq_date, brightness, confidence
            try:
                brightness = float(row.get("brightness", 0))
                event = {
                    "event_type": "Wildfire",
                    "region": f"{row.get('latitude','')},{row.get('longitude','')}",
                    "timestamp": f"{row.get('acq_date','')}T{row.get('acq_time','')}",
                    "severity": brightness_to_severity(brightness),
                    "source": "NASA FIRMS",
                    "description": f"Brightness: {brightness}, Confidence: {row.get('confidence','')}, FRP: {row.get('frp','')}"
                }
                events.append(event)
            except Exception as row_e:
                print(f"Row parse error: {row_e}")
    except Exception as e:
        print(f"NASA FIRMS API error: {e}")
    return events

def get_active_disaster_events() -> List[Dict[str, Any]]:
    """Return a list of normalized disaster events from all sources."""
    events = []
    events.extend(fetch_noaa_alerts())
    events.extend(fetch_nasa_firms_wildfires())
    return events
