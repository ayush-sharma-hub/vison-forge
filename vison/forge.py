"""Deterministic, safety-first project planning for Vison Forge."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
import json
import re

from .retailer import BuildTier, ComponentResearchService, PurchaseOption


SUPPORTED_PLATFORMS = ("arduino", "esp32", "raspberry pi", "robotics")
UNSAFE_TERMS = {
    "mains": "Mains electricity is outside Vison Forge's supported scope.",
    "220v": "Mains electricity is outside Vison Forge's supported scope.",
    "230v": "Mains electricity is outside Vison Forge's supported scope.",
    "110v": "Mains electricity is outside Vison Forge's supported scope.",
    "lipo": "High-current battery builds need specialist supervision and are outside this MVP.",
    "drone": "Drones are outside this MVP because they introduce flight and battery safety risks.",
    "medical": "Medical devices are outside this MVP.",
    "weapon": "Weapons are not supported.",
}


@dataclass(frozen=True)
class ForgeRequest:
    idea: str
    platform: str
    budget: float | None = None
    currency: str = "INR"
    deadline_days: int | None = None
    experience: str = "beginner"
    team_size: int = 1
    team_skills: tuple[str, ...] = ()
    available_parts: tuple[str, ...] = ()


@dataclass(frozen=True)
class Component:
    name: str
    quantity: int
    purpose: str
    voltage: str | None = None
    documentation_url: str | None = None
    purchase_status: str = "Purchase search pending"
    purchase_options: tuple[PurchaseOption, ...] = ()
    selected_option: PurchaseOption | None = None


@dataclass(frozen=True)
class ForgePlan:
    verdict: str
    summary: str
    safety_notes: tuple[str, ...]
    difficulty: str
    estimated_hours: int
    components: tuple[Component, ...]
    compatibility_notes: tuple[str, ...]
    wiring: tuple[str, ...]
    build_steps: tuple[str, ...]
    tests: tuple[str, ...]
    risks: tuple[str, ...]
    timeline: tuple[str, ...]
    team_tasks: tuple[str, ...]
    submission_checklist: tuple[str, ...]
    research_status: str
    tiers: tuple[BuildTier, ...] = ()
    estimated_total: float | None = None
    total_currency: str = "INR"
    total_is_complete: bool = False
    unpriced_components: tuple[str, ...] = ()
    disclaimer: str = ""


def _normalise(value: str) -> str:
    return value.strip().lower()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _project_kind(idea: str) -> str:
    lower = idea.lower()
    if _contains_any(lower, ("plant", "watering", "soil", "irrigation")):
        return "plant-monitor"
    if _contains_any(lower, ("line follower", "obstacle", "robot", "rover")):
        return "robot"
    return "iot"


def _components_for(request: ForgeRequest, kind: str) -> tuple[Component, ...]:
    platform = _normalise(request.platform)
    controller_name = "ESP32 development board" if platform == "esp32" else "Arduino Uno-compatible board"
    controller_docs = "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/" if platform == "esp32" else "https://docs.arduino.cc/hardware/uno-rev3/"
    base = [
        Component(controller_name, 1, "Main controller", "3.3V logic" if platform == "esp32" else "5V logic", controller_docs),
        Component("Breadboard", 1, "Safe temporary prototyping"),
        Component("Jumper wires", 1, "Low-voltage prototype connections"),
        Component("USB data cable", 1, "Programming and initial power"),
    ]
    if kind == "plant-monitor":
        base.extend((
            Component("Capacitive soil-moisture sensor", 2, "Measure soil moisture", "3.3V–5V"),
            Component("5V relay module with 3.3V-compatible input", 1, "Switch a low-voltage pump", "5V supply"),
            Component("Low-voltage 5V USB water pump", 1, "Water delivery; do not use mains power", "5V"),
            Component("Silicone tubing", 1, "Connect pump to plants"),
            Component("Separate 5V USB power source", 1, "Pump power; do not power pump from controller pin", "5V"),
        ))
    elif kind == "robot":
        base.extend((
            Component("Robot chassis with two DC motors", 1, "Mobile base", "3V–6V motors"),
            Component("Low-voltage motor driver module", 1, "Control motors without loading controller pins", "Motor supply per datasheet"),
            Component("Line sensors or ultrasonic sensor", 1, "Project input sensor", "3.3V–5V"),
            Component("AA battery holder or certified USB power bank", 1, "Low-risk portable power option"),
        ))
    else:
        base.append(Component("Sensor matched to the project goal", 1, "Collect the main project input", "Confirm from datasheet"))

    owned = {_normalise(item) for item in request.available_parts}
    return tuple(component for component in base if _normalise(component.name) not in owned)


def _safety_notes(request: ForgeRequest) -> tuple[str, ...]:
    text = request.idea.lower()
    notes = [message for term, message in UNSAFE_TERMS.items() if term in text]
    if _project_kind(request.idea) == "plant-monitor":
        notes.append("Keep water away from the controller and use only low-voltage, USB-powered equipment in this MVP.")
    return tuple(dict.fromkeys(notes))


def _difficulty(request: ForgeRequest, kind: str) -> tuple[str, int]:
    hours = {"plant-monitor": 10, "robot": 14, "iot": 8}[kind]
    if request.experience.lower() not in {"beginner", "student"}:
        hours = max(5, hours - 2)
    if request.deadline_days and request.deadline_days < 3:
        return "High — the deadline leaves little recovery time", hours
    if kind == "robot":
        return "Medium — mechanical, power, and software integration are required", hours
    return "Low to medium — suitable for a guided beginner build", hours


def _timeline(request: ForgeRequest, estimated_hours: int) -> tuple[str, ...]:
    days = request.deadline_days or 7
    days = max(1, min(days, 14))
    today = date.today()
    stages = ("Confirm parts and documentation", "Prototype one input/output", "Assemble the low-voltage circuit", "Implement core behaviour", "Calibrate and test failures", "Record demo and complete documentation")
    entries = []
    for index, stage in enumerate(stages):
        day_offset = min(index, days - 1)
        entries.append(f"Day {day_offset + 1} ({today + timedelta(days=day_offset):%d %b}): {stage}.")
    entries.append(f"Reserve the final day for recovery and submission; estimated hands-on work: about {estimated_hours} hours.")
    return tuple(entries)


def _team_tasks(request: ForgeRequest) -> tuple[str, ...]:
    roles = [
        "Hardware: verify components, assemble only the low-voltage circuit, and photograph each stage.",
        "Firmware: implement and test one subsystem at a time.",
        "Quality: run the test checklist and log failures/retests.",
        "Documentation: maintain README, BOM, demo script, and final submission evidence.",
    ]
    return tuple(roles[: max(1, min(request.team_size, len(roles)))])


def create_plan(
    request: ForgeRequest,
    research_service: ComponentResearchService | None = None,
    enable_live_research: bool = False,
) -> ForgePlan:
    """Create a conservative build plan without inventing prices or vendor listings."""
    platform = _normalise(request.platform)
    if platform not in SUPPORTED_PLATFORMS:
        return ForgePlan(
            verdict="Needs clarification",
            summary="Choose one supported platform: Arduino, ESP32, Raspberry Pi, or simple robotics.",
            safety_notes=(), difficulty="Unknown", estimated_hours=0, components=(), compatibility_notes=(), wiring=(),
            build_steps=(), tests=(), risks=(), timeline=(), team_tasks=(), submission_checklist=(),
            research_status="No source research was performed.",
        )
    safety = _safety_notes(request)
    if safety and any(term in request.idea.lower() for term in UNSAFE_TERMS):
        return ForgePlan(
            verdict="Scale down",
            summary=f"{safety[0]} Build a low-voltage simulation or seek qualified in-person supervision.",
            safety_notes=safety, difficulty="Unsupported safely", estimated_hours=0, components=(), compatibility_notes=(), wiring=(),
            build_steps=("Remove the unsafe element and restate the project using low-voltage, hobby-grade components.",), tests=(), risks=(), timeline=(), team_tasks=(), submission_checklist=(),
            research_status="No purchase research was performed for an unsupported request.",
        )

    kind = _project_kind(request.idea)
    difficulty, hours = _difficulty(request, kind)
    components = _components_for(request, kind)
    controller_pin = "GPIO 34" if platform == "esp32" else "A0"
    if kind == "plant-monitor":
        wiring = (
            f"Connect soil-sensor output to {controller_pin}; connect sensor power according to its datasheet.",
            "Connect the relay input to a free digital pin; relay VCC/GND must match its module documentation.",
            "Power the 5V pump from its separate 5V supply through the relay contacts; do not draw pump current from a controller pin.",
            "Keep all electronics dry and test the circuit before placing tubing near it.",
        )
        tests = (
            "Dry-sensor test: confirm the measured value changes when the sensor moves from dry air to water-free damp soil.",
            "Pump test: with water disconnected, trigger the relay for two seconds and confirm the controller remains powered.",
            "Fail-safe test: disconnect the sensor and confirm the pump does not run continuously.",
        )
        risks = ("Sensor readings drift; calibrate with dry and damp soil.", "Pump current can reset the controller; use separate low-voltage pump power.")
    elif kind == "robot":
        wiring = ("Connect motors to the motor-driver outputs, not directly to controller pins.", "Connect each sensor signal only after checking its logic voltage.", "Use the motor driver's datasheet before connecting the portable power source.")
        tests = ("Lift wheels off the surface for the first motor test.", "Test each sensor reading independently.", "Confirm a lost sensor signal stops the robot instead of driving indefinitely.")
        risks = ("Motor voltage/current mismatch can damage electronics.", "Mechanical alignment affects sensor accuracy.")
    else:
        wiring = ("Start with one sensor and the controller only.", "Confirm sensor supply and signal voltage from official documentation before wiring.")
        tests = ("Log ten sensor readings and check for plausible change.", "Disconnect the sensor and ensure the software reports a safe error state.")
        risks = ("The requested sensor is unspecified.", "Compatibility cannot be confirmed until the exact sensor model is selected.")

    build_steps = (
        "Read the linked controller documentation and confirm the board pin labels.",
        "Lay out the controller and one component without power; compare every connection to the wiring table.",
        "Test one input or output at a time using USB power only.",
        "Add the remaining components only after each prior test passes.",
        "Run the failure tests and record results in the build journal.",
    )
    checklist = ("Repository README", "Source-linked BOM", "Architecture/wiring explanation", "Test evidence", "Demo video", "Known limitations and safety notes")

    # Live Retailer Research Layer
    tiers: tuple[BuildTier, ...] = ()
    total: float | None = None
    total_curr: str = request.currency
    is_complete: bool = False
    unpriced: tuple[str, ...] = ()
    disclaimer: str = ComponentResearchService.DISCLAIMER

    if enable_live_research or research_service is not None:
        service = research_service or ComponentResearchService()
        updated_components: list[Component] = []
        component_data: list[tuple[str, int, list[PurchaseOption]]] = []

        for item in components:
            options = tuple(service.research_component(item.name))
            if options:
                selected = options[0]
                stock_label = (
                    "In stock" if selected.in_stock is True
                    else ("Out of stock" if selected.in_stock is False else "Stock unstated")
                )
                status = f"₹{selected.price:.2f} at {selected.seller} ({stock_label}) [Checked {selected.checked_at}]"
                updated_components.append(
                    Component(
                        name=item.name,
                        quantity=item.quantity,
                        purpose=item.purpose,
                        voltage=item.voltage,
                        documentation_url=item.documentation_url,
                        purchase_status=status,
                        purchase_options=options,
                        selected_option=selected,
                    )
                )
                component_data.append((item.name, item.quantity, list(options)))
            else:
                updated_components.append(
                    Component(
                        name=item.name,
                        quantity=item.quantity,
                        purpose=item.purpose,
                        voltage=item.voltage,
                        documentation_url=item.documentation_url,
                        purchase_status="Live pricing unavailable (retailer returned no options or source unreachable)",
                        purchase_options=(),
                        selected_option=None,
                    )
                )
                component_data.append((item.name, item.quantity, []))

        components = tuple(updated_components)
        tiers = tuple(service.build_tiers(component_data, currency=request.currency))
        selections = [(c.quantity, c.selected_option, c.name) for c in components]
        calc_total, calc_curr, is_complete, unpriced_list = service.calculate_total(selections, currency=request.currency)
        total = calc_total
        total_curr = calc_curr
        unpriced = tuple(unpriced_list)

        verified_count = sum(1 for c in components if c.selected_option is not None)
        if verified_count > 0:
            completeness_note = "all components verified" if is_complete else f"partial estimate, unpriced: {', '.join(unpriced)}"
            research_status = (
                f"Live retailer research verified via Quartz Components ({verified_count}/{len(components)} components verified; {completeness_note}). "
                f"Estimated project total: ₹{total:.2f}. See BOM for direct purchase links and price check timestamps."
            )
        else:
            research_status = (
                "Live retailer pricing was queried but no active listings were returned for these items. "
                "Prices remain marked unknown to prevent fabricating data."
            )
    else:
        research_status = (
            "Official controller documentation is linked. Live retailer price and stock research "
            "is available; no prices or purchase links are fabricated."
        )

    return ForgePlan(
        verdict="Ready",
        summary=f"A scoped {request.platform} {kind.replace('-', ' ')} project for a {request.experience} builder.",
        safety_notes=safety or ("Use only low-voltage hobby electronics and follow every component datasheet.",),
        difficulty=difficulty, estimated_hours=hours, components=components,
        compatibility_notes=("Controller pins must not power motors, pumps, or other high-current loads.", "Confirm the exact sensor's voltage and logic level before wiring."),
        wiring=wiring, build_steps=build_steps, tests=tests, risks=risks,
        timeline=_timeline(request, hours), team_tasks=_team_tasks(request), submission_checklist=checklist,
        research_status=research_status,
        tiers=tiers,
        estimated_total=total,
        total_currency=total_curr,
        total_is_complete=is_complete,
        unpriced_components=unpriced,
        disclaimer=disclaimer,
    )


def render_build_pack(request: ForgeRequest, plan: ForgePlan) -> dict[str, str]:
    """Render reusable Markdown artifacts, without writing them until requested."""
    component_lines = [
        "| Component | Qty | Purpose | Voltage | Verified seller | Displayed price | Stock | Direct purchase link | Checked |",
        "|---|---:|---|---|---|---:|---|---|---|",
    ]
    for item in plan.components:
        if item.selected_option:
            opt = item.selected_option
            stock = "In stock" if opt.in_stock is True else ("Out of stock" if opt.in_stock is False else "Unstated")
            component_lines.append(
                f"| {item.name} | {item.quantity} | {item.purpose} | {item.voltage or 'Confirm'} | {opt.seller} | ₹{opt.price:.2f} | {stock} | [Buy Option]({opt.url}) | {opt.checked_at} |"
            )
        else:
            component_lines.append(
                f"| {item.name} | {item.quantity} | {item.purpose} | {item.voltage or 'Confirm'} | — | Unavailable | — | — | {item.purchase_status} |"
            )

    tier_blocks = []
    if plan.tiers:
        tier_blocks.append("## Build Options (Tiers)\n")
        for tier in plan.tiers:
            status_text = "All items verified" if tier.is_complete else "Partial estimate"
            tier_blocks.append(f"### {tier.name} Build — ₹{tier.total_cost:.2f} ({status_text})\n{tier.description}\n")
            for sel in tier.selections:
                tier_blocks.append(f"- **{sel.component_query}**: ₹{sel.price:.2f} — [{sel.title}]({sel.url}) ({sel.seller})")
            tier_blocks.append("")

    total_block = ""
    if plan.estimated_total is not None:
        status_label = "Complete (all required items verified)" if plan.total_is_complete else f"Partial estimate; unpriced: {', '.join(plan.unpriced_components)}"
        total_block = (
            f"## Estimated Project Total\n\n"
            f"- **Estimated Total:** ₹{plan.estimated_total:.2f} {plan.total_currency}\n"
            f"- **Completeness:** {status_label}\n\n"
        )

    disclaimer_block = f"## Important Purchasing Policy\n\n{plan.disclaimer or ComponentResearchService.DISCLAIMER}\n"

    source_lines = [f"- [{item.name} documentation]({item.documentation_url})" for item in plan.components if item.documentation_url]
    build_plan = "\n".join(f"{number}. {step}" for number, step in enumerate(plan.build_steps, 1))
    return {
        "README.md": (
            f"# {request.idea}\n\n"
            f"## Vison Forge verdict\n\n**{plan.verdict}:** {plan.summary}\n\n"
            f"## Difficulty\n\n{plan.difficulty}\n\n"
            f"{total_block}"
            f"## Safety\n\n" + "\n".join(f"- {note}" for note in plan.safety_notes) + "\n\n"
            f"## Documentation\n\n" + ("\n".join(source_lines) or "- No documentation link available yet.") + "\n\n"
            f"{disclaimer_block}"
        ),
        "BOM.md": (
            "# Bill of Materials\n\n"
            + "\n".join(component_lines)
            + "\n\n"
            + total_block
            + "\n".join(tier_blocks)
            + "## Purchase research\n\n"
            + plan.research_status
            + "\n\n"
            + disclaimer_block
        ),
        "BUILD_PLAN.md": "# Build Plan\n\n" + build_plan + "\n\n## Wiring Blueprint\n\n" + "\n".join(f"- {line}" for line in plan.wiring),
        "TEST_PLAN.md": "# Test Plan\n\n" + "\n".join(f"- {item}" for item in plan.tests) + "\n\n## Risks\n\n" + "\n".join(f"- {item}" for item in plan.risks),
        "TASKS.md": "# Tasks and Timeline\n\n## Team tasks\n\n" + "\n".join(f"- {item}" for item in plan.team_tasks) + "\n\n## Timeline\n\n" + "\n".join(f"- {item}" for item in plan.timeline),
        "SUBMISSION.md": "# Hackathon Submission Checklist\n\n" + "\n".join(f"- [ ] {item}" for item in plan.submission_checklist),
    }


def save_build_pack(request: ForgeRequest, plan: ForgePlan, output_dir: Path) -> tuple[Path, ...]:
    """Write the build pack only to the caller-approved folder."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for filename, content in render_build_pack(request, plan).items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    journal = output_dir / "BUILD_JOURNAL.json"
    journal.write_text(json.dumps({"idea": request.idea, "completed": [], "next_action": plan.build_steps[0] if plan.build_steps else None}, indent=2), encoding="utf-8")
    paths.append(journal)
    return tuple(paths)


def update_build_journal(journal_path: Path, log_entry: str, next_action: str | None = None) -> dict:
    """Record user milestone progress in the local build journal."""
    from datetime import datetime, timezone
    if journal_path.exists():
        try:
            data = json.loads(journal_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            data = {"idea": "Hardware Project", "completed": []}
    else:
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"idea": "Hardware Project", "completed": []}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    record = {"entry": log_entry.strip(), "logged_at": timestamp}
    data.setdefault("completed", []).append(record)
    if next_action:
        data["next_action"] = next_action

    journal_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
