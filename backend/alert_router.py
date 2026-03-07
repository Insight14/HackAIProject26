"""Alert decision logic for incident risk outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AlertDecision:
    send_alert: bool
    priority: str
    channel: str
    audience: str
    message: str


def decide_alert(
    *,
    risk_score: float,
    risk_level: str,
    region: str,
    event_type: str,
    cause: str,
) -> AlertDecision:
    """Create an actionable alert decision based on risk level and context."""
    if risk_score >= 0.85:
        return AlertDecision(
            send_alert=True,
            priority="P1",
            channel="ops_sms",
            audience="grid_ops_and_incident_command",
            message=f"Critical {event_type} in {region} linked to {cause}. Immediate action required.",
        )

    if risk_score >= 0.7:
        return AlertDecision(
            send_alert=True,
            priority="P2",
            channel="ops_slack",
            audience="grid_ops_team",
            message=f"High-risk {event_type} in {region} linked to {cause}. Dispatch and monitor closely.",
        )

    if risk_score >= 0.5:
        return AlertDecision(
            send_alert=False,
            priority="P3",
            channel="dashboard",
            audience="operations_watch",
            message=f"Medium-risk {event_type} in {region}. Keep under active monitoring.",
        )

    return AlertDecision(
        send_alert=False,
        priority="P4",
        channel="log_only",
        audience="none",
        message=f"Low-risk {event_type} in {region}. No immediate alert needed.",
    )
