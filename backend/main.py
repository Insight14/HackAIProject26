"""FastAPI service for incident NLP parsing."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal

from backend.alert_router import decide_alert
from backend.disaster_events import get_active_disaster_events
from backend.incident_parser import parse_incident_text
from backend.gemini_recommender import suggest_response_actions
from backend.official_feed import CsvOfficialFeedAdapter
from backend.official_feed import ReplayApiOfficialFeedAdapter
from backend.replay_consumer import ReplayConsumer
from backend.risk_engine import score_incident_risk
from backend.event_classifier import *


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


app = FastAPI(title="Incident NLP Parser", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IncidentRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Raw incident report text")


class IncidentResponse(BaseModel):
    event_type: str
    cause: str
    severity: str
    severity_score: float
    region: str
    confidence: float


class RiskRequest(BaseModel):
    event_type: str
    cause: str
    severity: str
    severity_score: float = Field(..., ge=0.0, le=1.0)
    region: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class RiskResponse(BaseModel):
    risk_score: float
    risk_level: str
    recommended_action: str


class AlertRequest(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    region: str
    event_type: str
    cause: str


class AlertResponse(BaseModel):
    send_alert: bool
    priority: str
    channel: str
    audience: str
    message: str


class AnalyzeDecideRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Raw incident report text")


class AnalyzeDecideResponse(BaseModel):
    incident: IncidentResponse
    risk: RiskResponse
    alert: AlertResponse


class DatasetRefreshRequest(BaseModel):
    region: str = Field(default="USA", min_length=2, description="Region scope used by pipeline")
    hours: int = Field(default=24, ge=1, le=168, description="Recent hours of data to pull")
    output: str = Field(default="data/outages_latest.csv", description="Output CSV path")


class DatasetRefreshResponse(BaseModel):
    success: bool
    rows_written: int
    output_path: str
    region: str
    hours: int
    message: str
    logs: str | None = None


class DisasterEventResponse(BaseModel):
    event_type: str
    region: str
    timestamp: str
    severity: str
    source: str
    description: str


class SuggestionAction(BaseModel):
    priority: str
    owner: str
    timeframe: str
    action: str


class PlaybookStep(BaseModel):
    priority: str
    owner: str
    action: str


class SuggestionPlaybook(BaseModel):
    phase_0_15_min: list[PlaybookStep] = Field(default_factory=list, alias="0_15_min")
    phase_15_60_min: list[PlaybookStep] = Field(default_factory=list, alias="15_60_min")
    phase_60_240_min: list[PlaybookStep] = Field(default_factory=list, alias="60_240_min")


class SuggestResponseRequest(BaseModel):
    scenario_type: Literal["power_outage", "natural_disaster", "incident"] = "incident"
    title: str = Field(..., min_length=4, description="Short scenario title")
    description: str = Field(..., min_length=8, description="Detailed scenario description")
    region: str = Field(..., min_length=2)
    severity: str = Field(default="medium", min_length=3)
    affected_customers: int | None = Field(default=None, ge=0)


class SuggestResponseResponse(BaseModel):
    provider: str
    used_fallback: bool
    model: str
    scenario_type: str
    region: str
    severity: str
    title: str
    description: str
    assessment: str
    actions: list[SuggestionAction]
    playbook: SuggestionPlaybook | None = None
    evidence: list[str] = Field(default_factory=list)
    public_message: str
    confidence: float
    fallback_reason: str | None = None


class ReplayStatusResponse(BaseModel):
    source: str
    consumed_timestamp: str | None
    consumed_doc_id: str | None
    total_documents: int
    pending_documents: int
    next_timestamp: str | None
    next_doc_id: str | None


class ReplayNextRequest(BaseModel):
    batch_size: int = Field(default=1, ge=1, le=100)


class ReplayDocument(BaseModel):
    doc_id: str
    timestamp: str
    text: str
    source: str
    metadata: dict


class ReplayDecision(BaseModel):
    document: ReplayDocument
    incident: IncidentResponse
    risk: RiskResponse
    alert: AlertResponse


class ReplayNextResponse(BaseModel):
    consumed_count: int
    decisions: list[ReplayDecision]


class ReplayResetResponse(BaseModel):
    success: bool
    message: str


def _build_replay_consumer() -> tuple[ReplayConsumer, str]:
    repo_root = Path(__file__).resolve().parents[1]
    source = (os.getenv("OFFICIAL_FEED_SOURCE") or "csv").strip().lower()

    if source == "api":
        replay_url = os.getenv("OFFICIAL_FEED_REPLAY_URL", "").strip()
        if not replay_url:
            raise RuntimeError("OFFICIAL_FEED_REPLAY_URL must be set when OFFICIAL_FEED_SOURCE=api")
        adapter = ReplayApiOfficialFeedAdapter(url=replay_url)
    else:
        csv_rel = os.getenv("OFFICIAL_FEED_CSV_PATH", "data/outages_latest.csv").strip()
        adapter = CsvOfficialFeedAdapter(csv_path=repo_root / csv_rel)
        source = "csv"

    cursor_rel = os.getenv("OFFICIAL_FEED_CURSOR_PATH", "backend/.replay_cursor.json").strip()
    consumer = ReplayConsumer(adapter=adapter, cursor_path=repo_root / cursor_rel)
    return consumer, source


_replay_consumer, _replay_source = _build_replay_consumer()
_replay_lock = Lock()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/events", response_model=list[DisasterEventResponse])
def disaster_events() -> list[DisasterEventResponse]:
    events = get_active_disaster_events()
    return [DisasterEventResponse(**event) for event in events]


@app.post("/suggest_response", response_model=SuggestResponseResponse)
def suggest_response(payload: SuggestResponseRequest) -> SuggestResponseResponse:
    suggestion = suggest_response_actions(
        scenario_type=payload.scenario_type,
        title=payload.title,
        description=payload.description,
        region=payload.region,
        severity=payload.severity,
        affected_customers=payload.affected_customers,
    )

    return SuggestResponseResponse(**suggestion)


@app.post("/analyze_incident", response_model=IncidentResponse)
def analyze_incident(payload: IncidentRequest) -> IncidentResponse:
    signal = parse_incident_text(payload.text)
    return IncidentResponse(
        event_type=signal.event_type,
        cause=signal.cause,
        severity=signal.severity,
        severity_score=signal.severity_score,
        region=signal.region,
        confidence=signal.confidence,
    )


@app.post("/score_risk", response_model=RiskResponse)
def score_risk(payload: RiskRequest) -> RiskResponse:
    result = score_incident_risk(
        event_type=payload.event_type,
        cause=payload.cause,
        severity_score=payload.severity_score,
        confidence=payload.confidence,
    )
    return RiskResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        recommended_action=result.recommended_action,
    )


@app.post("/alert_decision", response_model=AlertResponse)
def alert_decision(payload: AlertRequest) -> AlertResponse:
    result = decide_alert(
        risk_score=payload.risk_score,
        risk_level=payload.risk_level,
        region=payload.region,
        event_type=payload.event_type,
        cause=payload.cause,
    )
    return AlertResponse(
        send_alert=result.send_alert,
        priority=result.priority,
        channel=result.channel,
        audience=result.audience,
        message=result.message,
    )


@app.post("/analyze_and_decide", response_model=AnalyzeDecideResponse)
def analyze_and_decide(payload: AnalyzeDecideRequest) -> AnalyzeDecideResponse:
    signal = parse_incident_text(payload.text)

    incident = IncidentResponse(
        event_type=signal.event_type,
        cause=signal.cause,
        severity=signal.severity,
        severity_score=signal.severity_score,
        region=signal.region,
        confidence=signal.confidence,
    )

    risk_result = score_incident_risk(
        event_type=incident.event_type,
        cause=incident.cause,
        severity_score=incident.severity_score,
        confidence=incident.confidence,
    )

    risk = RiskResponse(
        risk_score=risk_result.risk_score,
        risk_level=risk_result.risk_level,
        recommended_action=risk_result.recommended_action,
    )

    alert_result = decide_alert(
        risk_score=risk.risk_score,
        risk_level=risk.risk_level,
        region=incident.region,
        event_type=incident.event_type,
        cause=incident.cause,
    )

    alert = AlertResponse(
        send_alert=alert_result.send_alert,
        priority=alert_result.priority,
        channel=alert_result.channel,
        audience=alert_result.audience,
        message=alert_result.message,
    )

    return AnalyzeDecideResponse(incident=incident, risk=risk, alert=alert)


@app.post("/refresh_dataset", response_model=DatasetRefreshResponse)
def refresh_dataset(payload: DatasetRefreshRequest) -> DatasetRefreshResponse:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / payload.output

    command = [
        sys.executable,
        "-m",
        "src.pipeline.build_dataset",
        "--region",
        payload.region,
        "--hours",
        str(payload.hours),
        "--output",
        payload.output,
    ]

    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    logs = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Dataset refresh failed (exit {result.returncode}).\n{logs}",
        )

    if not output_path.exists():
        raise HTTPException(status_code=500, detail=f"Expected output file not found: {payload.output}")

    # Count data rows only (exclude header).
    with output_path.open("r", encoding="utf-8", errors="ignore") as f:
        rows_written = max(sum(1 for _ in f) - 1, 0)

    return DatasetRefreshResponse(
        success=True,
        rows_written=rows_written,
        output_path=payload.output,
        region=payload.region,
        hours=payload.hours,
        message=f"Refreshed dataset with {rows_written} rows.",
        logs=logs[-2000:] if logs else None,
    )


@app.get("/feed/replay/status", response_model=ReplayStatusResponse)
def replay_status() -> ReplayStatusResponse:
    with _replay_lock:
        status = _replay_consumer.status()

    return ReplayStatusResponse(source=_replay_source, **status)


@app.post("/feed/replay/reset", response_model=ReplayResetResponse)
def replay_reset() -> ReplayResetResponse:
    with _replay_lock:
        _replay_consumer.reset()

    return ReplayResetResponse(success=True, message="Replay cursor reset to start of feed.")


@app.post("/feed/replay/next", response_model=ReplayNextResponse)
def replay_next(payload: ReplayNextRequest) -> ReplayNextResponse:
    with _replay_lock:
        docs = _replay_consumer.consume_next(batch_size=payload.batch_size)

    decisions: list[ReplayDecision] = []
    for doc in docs:
        signal = parse_incident_text(doc.text)

        incident = IncidentResponse(
            event_type=signal.event_type,
            cause=signal.cause,
            severity=signal.severity,
            severity_score=signal.severity_score,
            region=signal.region,
            confidence=signal.confidence,
        )

        risk_result = score_incident_risk(
            event_type=incident.event_type,
            cause=incident.cause,
            severity_score=incident.severity_score,
            confidence=incident.confidence,
        )

        risk = RiskResponse(
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            recommended_action=risk_result.recommended_action,
        )

        alert_result = decide_alert(
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            region=incident.region,
            event_type=incident.event_type,
            cause=incident.cause,
        )

        alert = AlertResponse(
            send_alert=alert_result.send_alert,
            priority=alert_result.priority,
            channel=alert_result.channel,
            audience=alert_result.audience,
            message=alert_result.message,
        )

        replay_doc = ReplayDocument(
            doc_id=doc.doc_id,
            timestamp=doc.timestamp.isoformat(),
            text=doc.text,
            source=doc.source,
            metadata=doc.metadata,
        )

        decisions.append(ReplayDecision(document=replay_doc, incident=incident, risk=risk, alert=alert))

    return ReplayNextResponse(consumed_count=len(decisions), decisions=decisions)


@app.post("/api/send-alert-email")
async def send_alert_email(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        return {"error": "Email required"}
    try:
        msg = EmailMessage()
        msg.set_content("You are subscribed to outage alerts!")
        msg["Subject"] = "Outage Alert Signup"
        msg["From"] = "your_gmail@gmail.com"
        msg["To"] = email

        # Use your Gmail credentials (enable App Passwords if 2FA is on)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("your_gmail@gmail.com", "your_app_password")
            smtp.send_message(msg)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
