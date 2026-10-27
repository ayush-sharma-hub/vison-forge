"""AI Hardware Feasibility & Engineering Advisor powered by ASI:One.

Performs deep engineering analysis on any hardware project idea:
- If feasible: produces component breakdowns, pinout blueprints, and failure simulations.
- If infeasible/unsafe: provides a comprehensive engineering autopsy explaining
  why it cannot work (physics, compute, power, safety) and proposes safe alternatives.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_API_KEY = os.getenv("ASI_ONE_API_KEY")
_CLIENT = None

if _API_KEY:
    try:
        _CLIENT = OpenAI(
            base_url="https://api.asi1.ai/v1",
            api_key=_API_KEY,
            timeout=8.0,
        )
    except Exception:
        _CLIENT = None


@dataclass
class FeasibilityReport:
    is_buildable: bool
    verdict: str
    why_cannot_build: list[str]
    hazards: list[str]
    safe_alternative: str
    recommended_platform: str
    components: list[dict[str, Any]]
    wiring_blueprint: list[str]
    failure_symptom: str
    failure_root_cause: str
    failure_fix: str
    source: str = "ASI:One Neural Hardware Reasoning"


def analyze_hardware_query(user_query: str) -> FeasibilityReport | None:
    """Analyze any user hardware project using ASI:One's reasoning model."""
    if not _CLIENT:
        return None

    system_prompt = (
        "You are Vison Forge, an elite hardware prototyping mentor and embedded systems engineer. "
        "Analyze whether the user's hardware project is practically buildable by a student/hobbyist "
        "using safe, low-voltage hobby electronics (5V/3.3V Arduino, ESP32, Raspberry Pi). "
        "Strictly identify projects involving mains electricity (110V/220V), autonomous flying drones, "
        "weapons, high-power lasers, or impossible physics as NOT DIY buildable, and provide deep "
        "engineering explanations for why they fail and how to pivot to a safe alternative.\n"
        "Always respond with a valid, parseable JSON object only."
    )

    user_prompt = f"""Evaluate this project idea:
"{user_query}"

Respond with ONLY a JSON object formatted as:
{{
  "is_diy_buildable": true_or_false,
  "verdict": "Clear 1-line verdict",
  "why_cannot_build": [
    "Technical bottleneck 1 (physics, power, or compute constraints)",
    "Technical bottleneck 2"
  ],
  "hazards": [
    "Specific hazard 1 (e.g. LiPo fire, back-EMF, mains electrocution)",
    "Specific hazard 2"
  ],
  "safe_alternative": "A concrete, safe project the user can build instead using low-voltage hobby electronics",
  "recommended_platform": "Arduino Uno / Nano / ESP32 / Raspberry Pi",
  "components": [
    {{"name": "Component Name", "quantity": 1, "purpose": "Function in project", "voltage": "5V or 3.3V"}}
  ],
  "wiring_blueprint": [
    "Exact connection 1 (e.g. Servo Signal -> Arduino D9)",
    "Exact connection 2"
  ],
  "failure_simulation": {{
    "symptom": "What observed failure happens",
    "root_cause": "Physical / electrical root cause",
    "fix": "Hardware or firmware mitigation"
  }}
}}"""

    try:
        response = _CLIENT.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=900,
        )
        raw_text = response.choices[0].message.content or ""
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
        raw_text = re.sub(r"\s*```$", "", raw_text.strip())

        data = json.loads(raw_text)

        fail_sim = data.get("failure_simulation") or {}

        return FeasibilityReport(
            is_buildable=bool(data.get("is_diy_buildable", True)),
            verdict=str(data.get("verdict", "Feasibility Assessment Completed")),
            why_cannot_build=list(data.get("why_cannot_build", [])),
            hazards=list(data.get("hazards", [])),
            safe_alternative=str(data.get("safe_alternative", "")),
            recommended_platform=str(data.get("recommended_platform", "Arduino Uno")),
            components=list(data.get("components", [])),
            wiring_blueprint=list(data.get("wiring_blueprint", [])),
            failure_symptom=str(fail_sim.get("symptom", "Microcontroller reset or motor stall")),
            failure_root_cause=str(fail_sim.get("root_cause", "Voltage sag on supply rail")),
            failure_fix=str(fail_sim.get("fix", "Use separate power supply with common ground")),
        )
    except Exception:
        return None
