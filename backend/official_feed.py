"""Official feed adapters for timestamp-ordered replay consumption."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import requests


@dataclass(frozen=True)
class FeedDocument:
    """Canonical text document record emitted by feed adapters."""

    doc_id: str
    timestamp: datetime
    text: str
    source: str
    metadata: dict[str, Any]


class OfficialFeedAdapter(Protocol):
    """Source adapter contract for official timestamped text feed."""

    def load_documents(self) -> list[FeedDocument]:
        """Load all currently available documents from the feed source."""


class CsvOfficialFeedAdapter:
    """Reads a local CSV dataset file as an official replay feed source."""

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path

    def load_documents(self) -> list[FeedDocument]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Feed dataset file not found: {self.csv_path}")

        documents: list[FeedDocument] = []
        with self.csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                ts = _parse_timestamp(row.get("timestamp", ""))
                if ts is None:
                    continue

                text = _extract_text(row)
                if not text:
                    continue

                region = (row.get("region") or "unknown").strip() or "unknown"
                doc_id = _stable_doc_id(row=row, fallback_index=index, timestamp=ts)

                metadata = {
                    "region": region,
                    "raw": {k: (v or "") for k, v in row.items()},
                }

                documents.append(
                    FeedDocument(
                        doc_id=doc_id,
                        timestamp=ts,
                        text=text,
                        source="csv",
                        metadata=metadata,
                    )
                )

        return _sort_documents(documents)


class ReplayApiOfficialFeedAdapter:
    """Reads documents from an HTTP replay endpoint.

    Expected response body shape:
    {
      "documents": [
        {"id": "...", "timestamp": "...", "text": "...", "region": "...", ...}
      ]
    }
    """

    def __init__(self, url: str, timeout_seconds: float = 15.0) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def load_documents(self) -> list[FeedDocument]:
        response = requests.get(self.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()

        raw_docs = payload.get("documents", []) if isinstance(payload, dict) else []
        if not isinstance(raw_docs, list):
            raise ValueError("Replay API payload must contain a list under 'documents'.")

        documents: list[FeedDocument] = []
        for index, raw in enumerate(raw_docs):
            if not isinstance(raw, dict):
                continue

            ts = _parse_timestamp(str(raw.get("timestamp", "")))
            text = str(raw.get("text", "")).strip()
            if ts is None or not text:
                continue

            doc_id = str(raw.get("id") or "").strip() or f"api-{index}-{int(ts.timestamp())}"
            metadata = {k: v for k, v in raw.items() if k not in {"id", "timestamp", "text"}}

            documents.append(
                FeedDocument(
                    doc_id=doc_id,
                    timestamp=ts,
                    text=text,
                    source="replay_api",
                    metadata=metadata,
                )
            )

        return _sort_documents(documents)


def _parse_timestamp(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None

    candidate = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_text(row: dict[str, str]) -> str:
    disturbance = (row.get("disturbance_text") or "").strip()
    if disturbance:
        return disturbance

    fields = []
    for key in ["event_type", "event_cause", "event_severity", "weather_alert"]:
        value = (row.get(key) or "").strip()
        if value:
            fields.append(f"{key}={value}")

    return " | ".join(fields)


def _stable_doc_id(*, row: dict[str, str], fallback_index: int, timestamp: datetime) -> str:
    region = (row.get("region") or "unknown").strip() or "unknown"
    disturbance = (row.get("disturbance_text") or "").strip()
    token = disturbance[:40].replace(" ", "_") if disturbance else f"row{fallback_index}"
    return f"{region}-{int(timestamp.timestamp())}-{token}"


def _sort_documents(documents: list[FeedDocument]) -> list[FeedDocument]:
    # Strict ordering by timestamp then id ensures deterministic replay order.
    return sorted(documents, key=lambda x: (x.timestamp, x.doc_id))
