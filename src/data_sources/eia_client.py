from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd
import requests

from src.config import settings
from src.models import GridSnapshot


logger = logging.getLogger(__name__)


EIA_BASE_URL = "https://api.eia.gov/v2/electricity/rto"


def _require_api_key() -> str:
    if not settings.eia_api_key:
        raise RuntimeError(
            "EIA_API_KEY is not set. Please define it in your environment or .env file."
        )
    return settings.eia_api_key


def fetch_recent_grid_data(
    region: str,
    hours: int = 24,
) -> List[GridSnapshot]:
    """
    Fetch recent grid operations data for a region from EIA Open Data.

    This is intentionally conservative and focused on producing a few key
    fields for the outage risk pipeline: demand and generation by timestamp.

    Note: EIA's API has multiple datasets and balancing-authority codes.
    This function assumes the caller has configured a compatible region code.
    """
    api_key = _require_api_key()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    params: Dict[str, str] = {
        "api_key": api_key,
        "frequency": "hourly",
        "start": start_time.strftime("%Y-%m-%dT%H"),
        "end": end_time.strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": "0",
        "length": "5000",
    }

    # This URL and params are a reasonable starting point but may need
    # refinement once you lock in the exact EIA dataset and region codes.
    url = f"{EIA_BASE_URL}/region-data/data"

    logger.info("Requesting EIA data for region=%s", region)
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    records = payload.get("response", {}).get("data", [])
    if not records:
        logger.warning("No EIA data returned for region=%s", region)
        return []

    df = pd.DataFrame.from_records(records)

    # Attempt to map typical EIA field names; adjust once actual schema is confirmed.
    snapshots: List[GridSnapshot] = []
    for _, row in df.iterrows():
        timestamp_str: Optional[str] = row.get("period")
        if not timestamp_str:
            continue

        try:
            ts = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
        except Exception:
            logger.debug("Skipping row with invalid period=%s", timestamp_str)
            continue

        demand = _safe_float(row.get("demand"))
        generation = _safe_float(row.get("generation"))

        snapshots.append(
            GridSnapshot(
                region=region,
                timestamp=ts,
                demand_mw=demand,
                generation_mw=generation,
            )
        )

    return snapshots


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

