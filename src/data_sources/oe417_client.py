from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import requests

from src.models import DisturbanceEvent


logger = logging.getLogger(__name__)


OE417_CSV_URL = (
    "https://www.oe.netl.doe.gov/downloads/OE417_annual_summary.csv"
)


def fetch_oe417_events() -> List[DisturbanceEvent]:
    """
    Fetch DOE OE-417 annual summary data and convert to disturbance events.

    The exact CSV schema may vary by year; this implementation focuses on
    a few common-sense columns and is easy to adapt once the real schema
    is confirmed.
    """
    logger.info("Downloading OE-417 annual summary from %s", OE417_CSV_URL)
    response = requests.get(OE417_CSV_URL, timeout=60)
    response.raise_for_status()

    content = response.content.decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))

    events: List[DisturbanceEvent] = []

    for _, row in df.iterrows():
        ts = _parse_timestamp(
            row.get("Date Event Began")
            or row.get("Event Date")
            or row.get("DATE")
        )
        if ts is None:
            continue

        region = str(
            row.get("NERC Region")
            or row.get("Region")
            or row.get("State")
            or "Unknown"
        ).strip()

        cause = _string_or_none(
            row.get("Cause")
            or row.get("Event Cause")
        )

        event_type = _string_or_none(
            row.get("Event Type")
            or row.get("Type of Disturbance")
        )

        severity = _string_or_none(
            row.get("Severity")
            or row.get("Demand Loss (MW)")
        )

        # Create a raw text field combining key info for NLP.
        raw_pieces = [
            _string_or_none(row.get("Event Description")),
            _string_or_none(row.get("Remarks")),
        ]
        raw_text = " ".join(p for p in raw_pieces if p)
        raw_text = raw_text or None

        events.append(
            DisturbanceEvent(
                region=region,
                timestamp=ts,
                event_type=event_type,
                cause=cause,
                severity=str(severity) if severity is not None else None,
                raw_text=raw_text,
            )
        )

    return events


def _parse_timestamp(value: object) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Try a few common date formats; adjust as needed.
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    logger.debug("Unable to parse OE-417 timestamp: %s", text)
    return None


def _string_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

