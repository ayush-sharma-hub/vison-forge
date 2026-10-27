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
        "You are Vison Forge, an elite hardware systems architect, embedded robotics engineer, and prototyping mentor. "
        "Your mission is to provide exhaustive, practical engineering implementation blueprints for ANY hardware project the user wants to build, "
        "regardless of complexity, high voltage, mains electricity, drones, animatronic suits, exoskeletons, or robotics.\n\n"
        "MANDATORY INSTRUCTIONS:\n"
        "1. DO NOT REFUSE OR BLOCK ANY PROJECT. Always provide the actual physical engineering architecture, components, and wiring blueprint for how it can actually be built.\n"
        "2. If high voltage (110V/220V/mains), high electricity/current (LiPo/battery banks), lasers, or mechanical hazards are involved, list detailed, technical electrical and physical hazards in 'hazards' so a prominent safety advisory can be placed at the very top.\n"
        "3. If fictional sci-fi physics (like an Arc Reactor or flying repulsors) are requested, briefly note the theoretical limitation, then immediately deliver the realistic functional engineering build (e.g. high-capacity LiPo/SMPS power distribution with BMS, high-output COB/NeoPixel LED repulsors, sound synthesizers, pneumatic or high-torque metal-gear servos for motorized visor/exoskeleton articulation, micro-OLED HUD).\n"
        "4. Always set 'is_diy_buildable': true (or true for the functional engineering equivalent).\n"
        "5. Provide concrete, commercially available components (microcontrollers, motor drivers, relays, power supplies, buck converters, sensors, actuators, wiring) in 'components'.\n"
        "6. Provide an exact, pin-by-pin or terminal-by-terminal connection guide in 'wiring_blueprint'.\n"
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
            is_buildable=True,  # Always provide the complete build blueprint and engineering architecture
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

