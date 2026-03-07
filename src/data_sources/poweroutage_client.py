from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import requests

from src.models import GridSnapshot


logger = logging.getLogger(__name__)


ODIN_BASE_URL = (
    "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/"
    "odin-real-time-outages-county/records"
)


def fetch_poweroutage_snapshots(region: str) -> List[GridSnapshot]:
    """
    Fetch county-level outage snapshots from ORNL ODIN free public API.

    Notes:
    - This endpoint is public and does not require an API key.
        - `region` is treated as a state name (e.g., "California") for filtering.
            Passing "USA"/"US"/"ALL" fetches unfiltered nationwide records.
    - ODIN is outage-incident oriented, so demand/generation are not available
      and remain unset in GridSnapshot.
    """
    params = {
        "select": (
            "state,county,name,metersaffected,reportedstarttime,"
            "estimatedrestorationtime,incident_cause,statuskind"
        ),
        "limit": 100,
    }

    normalized_region = (region or "").strip()
    if normalized_region and normalized_region.lower() not in {"all", "us", "usa"}:
        # ODSQL string filtering. Keep it simple and avoid shell injection style
        # characters since this comes from user-facing inputs.
        safe_region = normalized_region.replace("'", "''")
        params["where"] = f"state = '{safe_region}'"

    logger.info("Requesting ODIN outage data for region=%s", normalized_region or "ALL")
    response = requests.get(ODIN_BASE_URL, params=params, timeout=45)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("results", [])
    if not records:
        logger.warning("No ODIN outage records returned for region=%s", region)
        return []

    snapshots: List[GridSnapshot] = []
    for rec in records:
        timestamp = _parse_odin_timestamp(
            rec.get("reportedstarttime") or rec.get("estimatedrestorationtime")
        )
        if timestamp is None:
            # Skip records with no meaningful timestamp.
            continue

        state = _clean_text(rec.get("state")) or normalized_region or "Unknown"
        county = _clean_text(rec.get("county"))
        utility = _clean_text(rec.get("name"))
        cause = _clean_text(rec.get("incident_cause"))
        status = _clean_text(rec.get("statuskind"))
        affected = rec.get("metersaffected")

        pieces = [
            f"Utility={utility}" if utility else None,
            f"County={county}" if county else None,
            f"MetersAffected={affected}" if affected is not None else None,
            f"Cause={cause}" if cause else None,
            f"Status={status}" if status else None,
        ]
        disturbance_text = " | ".join(p for p in pieces if p) or None

        snapshots.append(
            GridSnapshot(
                region=state,
                timestamp=timestamp,
                disturbance_text=disturbance_text,
            )
        )

    return snapshots


def _parse_odin_timestamp(value: object) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Common ODIN format: 2026-03-07T19:49:00+00:00
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        logger.debug("Unable to parse ODIN timestamp: %s", text)
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _clean_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

