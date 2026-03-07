from __future__ import annotations

import logging
from typing import List

from src.models import GridSnapshot


logger = logging.getLogger(__name__)


def fetch_poweroutage_snapshots(region: str) -> List[GridSnapshot]:
    """
    Placeholder for poweroutage.us integration.

    The public poweroutage.us site does not expose a simple, documented JSON
    API, and usage terms may restrict scraping. This function is left as a
    stub so it can be wired up later with either:

    - An official API (if available), or
    - A one-off CSV export / cached dataset for hackathon purposes.
    """
    logger.warning(
        "fetch_poweroutage_snapshots is a placeholder and currently returns an empty list."
    )
    return []

