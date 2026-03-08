"""Timestamp-ordered replay consumer with persisted watermark cursor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from official_feed import FeedDocument, OfficialFeedAdapter


@dataclass
class ReplayCursor:
    """Persistent watermark that marks the last consumed document."""

    timestamp: datetime | None = None
    doc_id: str | None = None


class ReplayConsumer:
    """Consumes documents in strict timestamp order from an official feed adapter."""

    def __init__(self, adapter: OfficialFeedAdapter, cursor_path: Path) -> None:
        self.adapter = adapter
        self.cursor_path = cursor_path
        self.cursor = self._load_cursor()

    def status(self) -> dict[str, str | int | None]:
        all_docs = self.adapter.load_documents()
        pending = self._pending_docs(all_docs)

        return {
            "consumed_timestamp": self.cursor.timestamp.isoformat() if self.cursor.timestamp else None,
            "consumed_doc_id": self.cursor.doc_id,
            "total_documents": len(all_docs),
            "pending_documents": len(pending),
            "next_timestamp": pending[0].timestamp.isoformat() if pending else None,
            "next_doc_id": pending[0].doc_id if pending else None,
        }

    def reset(self) -> None:
        self.cursor = ReplayCursor(timestamp=None, doc_id=None)
        self._save_cursor()

    def consume_next(self, batch_size: int = 1) -> list[FeedDocument]:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        all_docs = self.adapter.load_documents()
        pending = self._pending_docs(all_docs)
        selected = pending[:batch_size]

        if selected:
            last = selected[-1]
            self.cursor = ReplayCursor(timestamp=last.timestamp, doc_id=last.doc_id)
            self._save_cursor()

        return selected

    def _pending_docs(self, all_docs: list[FeedDocument]) -> list[FeedDocument]:
        if self.cursor.timestamp is None:
            return all_docs

        pending: list[FeedDocument] = []
        watermark = self.cursor.timestamp
        watermark_id = self.cursor.doc_id or ""

        for doc in all_docs:
            if doc.timestamp > watermark:
                pending.append(doc)
                continue

            if doc.timestamp == watermark and doc.doc_id > watermark_id:
                pending.append(doc)

        return pending

    def _load_cursor(self) -> ReplayCursor:
        if not self.cursor_path.exists():
            return ReplayCursor()

        raw = json.loads(self.cursor_path.read_text(encoding="utf-8"))
        ts = raw.get("timestamp")
        doc_id = raw.get("doc_id")

        if not ts:
            return ReplayCursor(timestamp=None, doc_id=None)

        try:
            parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            return ReplayCursor(timestamp=None, doc_id=None)

        return ReplayCursor(timestamp=parsed, doc_id=str(doc_id) if doc_id else None)

    def _save_cursor(self) -> None:
        self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": self.cursor.timestamp.isoformat() if self.cursor.timestamp else None,
            "doc_id": self.cursor.doc_id,
        }
        self.cursor_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
