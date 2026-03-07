"""FastAPI service for incident NLP parsing."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from alert_router import decide_alert
from incident_parser import parse_incident_text
from risk_engine import score_incident_risk


app = FastAPI(title="Incident NLP Parser", version="1.0.0")


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
