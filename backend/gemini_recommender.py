"""Gemini-backed response recommendation helper with safe fallback behavior."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def suggest_response_actions(
    *,
    scenario_type: str,
    title: str,
    description: str,
    region: str,
    severity: str,
    affected_customers: int | None,
) -> dict[str, Any]:
    """Generate response suggestions for outage/disaster scenarios."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _fallback_suggestion(
            scenario_type=scenario_type,
            title=title,
            description=description,
            region=region,
            severity=severity,
            affected_customers=affected_customers,
            reason="Missing GEMINI_API_KEY",
        )

    prompt = _build_prompt(
        scenario_type=scenario_type,
        title=title,
        description=description,
        region=region,
        severity=severity,
        affected_customers=affected_customers,
    )

    try:
        url = _GEMINI_ENDPOINT.format(model=_GEMINI_MODEL)
        response = requests.post(
            f"{url}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            },
            timeout=20,
        )
        response.raise_for_status()

        payload = response.json()
        text = _extract_text(payload)
        parsed = _extract_json(text)

        if not isinstance(parsed, dict):
            raise ValueError("Gemini response was not a JSON object")

        return {
            "provider": "gemini",
            "used_fallback": False,
            "model": _GEMINI_MODEL,
            "scenario_type": scenario_type,
            "region": region,
            "severity": severity,
            "title": title,
            "description": description,
            "assessment": str(parsed.get("assessment", "")),
            "actions": parsed.get("actions", []),
            "public_message": str(parsed.get("public_message", "")),
            "confidence": float(parsed.get("confidence", 0.7)),
        }
    except Exception as exc:  # noqa: BLE001
        return _fallback_suggestion(
            scenario_type=scenario_type,
            title=title,
            description=description,
            region=region,
            severity=severity,
            affected_customers=affected_customers,
            reason=str(exc),
        )


def _build_prompt(
    *,
    scenario_type: str,
    title: str,
    description: str,
    region: str,
    severity: str,
    affected_customers: int | None,
) -> str:
    customers_text = "unknown" if affected_customers is None else str(affected_customers)
    return f"""
You are a grid operations advisor.
Return ONLY valid JSON (no markdown, no prose) with this schema:
{{
  "assessment": "one-paragraph tactical assessment",
  "actions": [
    {{
      "priority": "P1|P2|P3",
      "owner": "team name",
      "timeframe": "e.g. 0-15 min",
      "action": "specific actionable step"
    }}
  ],
  "public_message": "short public-safe status update",
  "confidence": 0.0
}}

Constraints:
- Generate 4 to 6 actions.
- Actions must be realistic for utility outage and disaster response playbooks.
- For power outages, include restoration, crew dispatch, and critical-infrastructure checks.
- For natural disasters, include emergency coordination and protective shutoff/containment when relevant.
- confidence must be between 0 and 1.

Scenario:
- type: {scenario_type}
- title: {title}
- description: {description}
- region: {region}
- severity: {severity}
- affected_customers: {customers_text}
""".strip()


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini returned no text parts")

    text = parts[0].get("text")
    if not text:
        raise ValueError("Gemini returned an empty text part")
    return text


def _extract_json(text: str) -> Any:
    cleaned = text.strip()

    # Handles fenced blocks if model includes markdown despite instruction.
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    return json.loads(cleaned)


def _fallback_suggestion(
    *,
    scenario_type: str,
    title: str,
    description: str,
    region: str,
    severity: str,
    affected_customers: int | None,
    reason: str,
) -> dict[str, Any]:
    sev = severity.lower()
    high = sev in {"high", "critical"}
    customers = affected_customers or 0

    base_actions = [
        {
            "priority": "P1" if high else "P2",
            "owner": "Grid Operations",
            "timeframe": "0-15 min",
            "action": f"Open incident command channel and verify outage/disaster scope for {region}.",
        },
        {
            "priority": "P1" if high else "P2",
            "owner": "Field Dispatch",
            "timeframe": "15-30 min",
            "action": "Dispatch nearest available crew and confirm safe access routes.",
        },
        {
            "priority": "P2",
            "owner": "Critical Infrastructure Liaison",
            "timeframe": "15-45 min",
            "action": "Contact hospitals, water systems, and telecom operators for backup power readiness.",
        },
        {
            "priority": "P2",
            "owner": "Public Information",
            "timeframe": "30-60 min",
            "action": "Publish a status update with impacted areas and expected next update window.",
        },
    ]

    if scenario_type == "natural_disaster":
        base_actions.append(
            {
                "priority": "P1" if high else "P2",
                "owner": "Emergency Management",
                "timeframe": "0-30 min",
                "action": "Coordinate with county/state emergency operations center and align protective actions.",
            }
        )

    if customers > 5000:
        base_actions.append(
            {
                "priority": "P1",
                "owner": "Mutual Aid Coordinator",
                "timeframe": "30-60 min",
                "action": "Initiate mutual-aid standby for potential multi-day restoration support.",
            }
        )

    return {
        "provider": "fallback",
        "used_fallback": True,
        "model": _GEMINI_MODEL,
        "scenario_type": scenario_type,
        "region": region,
        "severity": severity,
        "title": title,
        "description": description,
        "assessment": (
            f"{title} in {region} is being treated as {'high' if high else 'moderate'} operational risk. "
            "Recommended actions prioritize stabilization, crew safety, and critical-service continuity."
        ),
        "actions": base_actions,
        "public_message": (
            f"Utility response is active for {region}. Crews are assessing impact and coordinating restoration steps."
        ),
        "confidence": 0.55 if high else 0.45,
        "fallback_reason": reason,
    }
