from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

import pandas as pd

from src.config import settings
from src.data_sources.eia_client import fetch_recent_grid_data
from src.data_sources.oe417_client import fetch_oe417_events
from src.data_sources.poweroutage_client import fetch_poweroutage_snapshots
from src.models import GridSnapshot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def build_unified_dataset(region: str, hours: int) -> pd.DataFrame:
    """
    Pull data from multiple sources and emit a unified outage-risk-friendly dataset.
    """
    logger.info("Building unified dataset for region=%s hours=%d", region, hours)

    # 1) Grid data from EIA
    eia_snapshots: List[GridSnapshot] = fetch_recent_grid_data(region, hours=hours)

    # 2) Disturbance incidents from OE-417
    oe_events = fetch_oe417_events()

    # 3) (Optional) Poweroutage.us data, currently a stub
    po_snapshots = fetch_poweroutage_snapshots(region)

    # Convert GridSnapshot objects to DataFrame
    grid_rows = [
        {
            "region": s.region,
            "timestamp": s.timestamp,
            "demand_mw": s.demand_mw,
            "generation_mw": s.generation_mw,
            "weather_alert": s.weather_alert,
            "disturbance_text": s.disturbance_text,
        }
        for s in eia_snapshots + po_snapshots
    ]
    grid_df = pd.DataFrame(grid_rows)

    # Convert OE-417 disturbance events into a text field we can later feed to NLP
    oe_rows = [
        {
            "region": e.region,
            "timestamp": e.timestamp,
            "disturbance_text": e.raw_text,
            "event_type": e.event_type,
            "event_cause": e.cause,
            "event_severity": e.severity,
        }
        for e in oe_events
    ]
    oe_df = pd.DataFrame(oe_rows)

    # Outer-join on region + timestamp (coarse alignment); further refinement
    # is possible if needed.
    if not grid_df.empty and not oe_df.empty:
        merged = pd.merge_asof(
            grid_df.sort_values("timestamp"),
            oe_df.sort_values("timestamp"),
            on="timestamp",
            by="region",
            direction="nearest",
            tolerance=pd.Timedelta("3H"),
        )
    else:
        merged = grid_df if not grid_df.empty else oe_df

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a unified outage-risk dataset from public sources."
    )
    parser.add_argument(
        "--region",
        type=str,
        default=settings.default_region,
        help="Region / balancing authority name (logical label used in the pipeline).",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many recent hours of grid data to fetch.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/outages_latest.csv",
        help="Path to the output CSV file.",
    )

    args = parser.parse_args()

    df = build_unified_dataset(region=args.region, hours=args.hours)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Writing %d rows to %s", len(df), output_path)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()

