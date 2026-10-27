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
    "mains": "Mains AC voltage (110V-230V): Use an isolated industrial SMPS, GFCI breaker, and fused relay optocouplers with zero exposed conductors.",
    "220v": "220V AC electricity: Requires optoisolated relays, PCB creepage distance >6mm, and certified earthed metal enclosure.",
    "230v": "230V AC electricity: Requires optoisolated relays, PCB creepage distance >6mm, and certified earthed metal enclosure.",
    "110v": "110V AC electricity: Requires optoisolated relays, PCB creepage distance >6mm, and certified earthed metal enclosure.",
    "high voltage": "High-voltage subsystem: Must incorporate galvanic isolation, flyback diodes, and dedicated earthing.",
    "electricity": "Electrical high current: Dedicated power distribution rails with common star-grounding are required.",
    "lipo": "Lithium Polymer / Li-ion batteries: A dedicated Battery Management System (BMS) with overcurrent, balancing, and thermal cutoff is mandatory.",
    "drone": "Autonomous flight propellers: Hardware kill-switch, propeller safety guards, and radio fail-safe logic are required.",
    "medical": "Medical-grade equipment: Requires redundant safety cutoffs, optoisolation, and clinical safety compliance.",
    "weapon": "Kinetic/repulsor/high-energy mechanism: Physical interlocks, electronic dead-man switches, and blast/pinch-proof barriers required.",
    "laser": "Laser diodes: Use certified safety goggles (OD 5+ rating) matched to the laser wavelength and active beam warning indicators.",
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
    if _contains_any(lower, ("door lock", "smart lock", "smart door", "rfid", "solenoid", "access control")):
        return "smart-lock"
    if _contains_any(lower, ("weather", "weather station", "bme280", "rain")):
        return "weather-station"
    if _contains_any(lower, ("home automation", "smart home")):
        return "home-automation"
    if _contains_any(lower, ("iron man", "suit", "animatronic", "wearable", "exoskeleton", "cosplay", "helmet", "armor")):
        return "wearable-animatronic"
    return "iot"


def _components_for(request: ForgeRequest, kind: str) -> tuple[Component, ...]:
    platform = _normalise(request.platform)

    if platform == "esp32":
        controller_name = "ESP32 development board"
        controller_voltage = "3.3V logic"
        controller_docs = "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/"
        usb_cable = "Micro USB / USB-C data cable"
    elif platform == "raspberry pi":
        controller_name = "Raspberry Pi 4 Model B (2GB)"
        controller_voltage = "5V via USB-C"
        controller_docs = "https://www.raspberrypi.com/documentation/"
        usb_cable = "USB-C power cable and micro-SD card (16GB+)"
    else:  # arduino and robotics
        controller_name = "Arduino Uno-compatible board"
        controller_voltage = "5V logic"
        controller_docs = "https://docs.arduino.cc/hardware/uno-rev3/"
        usb_cable = "USB-B data cable"

    base = [
        Component(controller_name, 1, "Main controller", controller_voltage, controller_docs),
        Component("Breadboard", 1, "Safe temporary prototyping"),
        Component("Jumper wires", 1, "Low-voltage prototype connections"),
        Component(usb_cable, 1, "Programming and initial power"),
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
    elif kind == "smart-lock":
        base.extend((
            Component("RFID-RC522 reader module", 1, "Read RFID/NFC access cards", "3.3V"),
            Component("12V solenoid lock (door latch)", 1, "Electric door latch actuator", "12V DC — use relay isolation, never from MCU"),
            Component("5V relay module with 3.3V-compatible input", 1, "Safely switch 12V solenoid from 3.3V MCU signal", "5V coil"),
            Component("12V DC power adapter (1a+)", 1, "Power for solenoid — isolated from MCU rail", "12V"),
            Component("LED indicators (green + red)", 2, "Access granted / denied feedback", "3.3V via 220 Ohm resistor"),
        ))
    elif kind == "weather-station":
        base.extend((
            Component("BME280 temperature/humidity/pressure sensor", 1, "Environmental sensing", "3.3V I2C"),
            Component("Rain detector module", 1, "Detect precipitation", "3.3V–5V digital output"),
            Component("0.96 inch I2C OLED Display Module", 1, "Local data display", "3.3V"),
        ))
    elif kind == "home-automation":
        base.extend((
            Component("4-channel relay module with optocoupler", 1, "Switch AC/DC loads safely", "5V coil, 3.3V-compatible input"),
            Component("DHT22 digital temperature and humidity sensor", 1, "Environmental monitoring", "3.3V–5V"),
            Component("HC-SR501 PIR motion sensor module", 1, "Occupancy detection for automation", "5V"),
        ))
    elif kind == "wearable-animatronic":
        base.extend((
            Component("MG996R Metal Gear High-Torque Servo Motor", 2, "Actuate helmet visor opening and closing mechanism", "5V–6V (high stall current 1.5A)"),
            Component("WS2812B Addressable RGB NeoPixel 16-LED Ring", 2, "Repulsor palm and Arc Reactor glowing effect", "5V DC"),
            Component("DFPlayer Mini MP3 Player Module", 1, "High-fidelity repulsor blast and Jarvis audio effects", "3.3V–5V"),
            Component("8 Ohm 3W Audio Speaker with Enclosure", 1, "Audio playback in helmet or chest", "3W"),
            Component("LM2596 DC-DC 5A Step-Down Buck Converter", 1, "Dedicated regulated 5V power rail for servos (isolates MCU)", "Input 7V-30V, Output 5V"),
            Component("PCA9685 16-Channel 12-Bit PWM I2C Servo Driver", 1, "Jitter-free multi-servo control without loading MCU timers", "5V VCC, 3.3V/5V I2C"),
            Component("MPU-6050 6-DOF Accelerometer and Gyroscope", 1, "Palm tilt and head-motion gesture detection", "3.3V I2C"),
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
    hours = {"plant-monitor": 10, "robot": 14, "iot": 8, "smart-lock": 12, "weather-station": 8, "home-automation": 12, "wearable-animatronic": 16}.get(kind, 8)
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
    # Do NOT block or scale down: attach safety notes so they render as a high-visibility warning on top!

    kind = _project_kind(request.idea)
    difficulty, hours = _difficulty(request, kind)
    components = _components_for(request, kind)

    if platform == "esp32":
        controller_pin = "GPIO 34"
        compat_note = "ESP32 GPIO pins operate at 3.3V logic — never connect 5V signals directly to GPIO pins."
    elif platform == "raspberry pi":
        controller_pin = "GPIO 17 (BCM numbering)"
        compat_note = "Raspberry Pi GPIO pins operate at 3.3V. Use a level-shifter for any 5V sensor signals."
    else:
        controller_pin = "A0"
        compat_note = "Arduino Uno GPIO pins operate at 5V logic — confirm sensor compatibility before wiring."
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
        compatibility_notes=(
            "Controller pins must not power motors, pumps, or other high-current loads.",
            compat_note,
            "Confirm the exact sensor's voltage and logic level before wiring.",
        ),
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


def render_detailed_wiring(request: ForgeRequest, plan: ForgePlan) -> str:
    """Generate an authoritative pin-to-pin text wiring blueprint and power topology."""
    lower_idea = request.idea.lower()
    platform = _normalise(request.platform)
    kind = _project_kind(request.idea)

    if kind == "robot" or "robot" in lower_idea or "obstacle" in lower_idea or "line" in lower_idea:
        is_nano = "nano" in lower_idea
        mcu_name = "Arduino Nano V3" if is_nano else ("ESP32 DevKit" if platform == "esp32" else "Arduino Uno R3")
        mcu_voltage = "3.3V" if platform == "esp32" else "5V"

        table = [
            "| Module / Subsystem | Module Pin | Controller / Supply Rail | Wire Type | Voltage & Signal Notes |",
            "|---|---|---|---|---|",
            f"| L298N Motor Driver | IN1 (Motor A Dir) | {mcu_name} D8 | Jumper (F-to-M) | 5V Logic control signal |",
            f"| L298N Motor Driver | IN2 (Motor A Dir) | {mcu_name} D9 | Jumper (F-to-M) | 5V Logic control signal |",
            f"| L298N Motor Driver | IN3 (Motor B Dir) | {mcu_name} D10 | Jumper (F-to-M) | 5V Logic control signal |",
            f"| L298N Motor Driver | IN4 (Motor B Dir) | {mcu_name} D11 | Jumper (F-to-M) | 5V Logic control signal |",
            "| L298N Motor Driver | 12V / VMS Power | Battery Pack Positive (+) | Stranded Wire | 6V–12V External Motor Rail (Do NOT power from MCU!) |",
            f"| L298N Motor Driver | GND (Power Ground) | Battery (-) **AND** {mcu_name} GND | Stranded Wire | **MANDATORY COMMON GROUND** for reference voltage |",
            "| L298N Motor Driver | OUT1, OUT2 | Left DC Gearmotor | Stranded Wire | Bi-directional H-Bridge motor output |",
            "| L298N Motor Driver | OUT3, OUT4 | Right DC Gearmotor | Stranded Wire | Bi-directional H-Bridge motor output |",
            f"| Left IR Sensor Module | OUT (Digital) | {mcu_name} D2 (Interrupt pin) | Jumper (F-to-M) | Active LOW obstacle detection |",
            f"| Left IR Sensor Module | VCC, GND | {mcu_name} 5V rail, GND | Jumper (F-to-M) | Sensor operating power |",
            f"| Right IR Sensor Module | OUT (Digital) | {mcu_name} D3 (Interrupt pin) | Jumper (F-to-M) | Active LOW obstacle detection |",
            f"| Right IR Sensor Module | VCC, GND | {mcu_name} 5V rail, GND | Jumper (F-to-M) | Sensor operating power |",
            f"| HC-SR04 Ultrasonic (opt)| Trig / Echo | {mcu_name} D12 / D13 | Jumper (F-to-M) | 10µs trigger pulse, Echo duration measure |",
            f"| Microcontroller Power | USB / VIN | 5V USB Power Bank or 5V Reg | USB Cable | Isolated from high-current motor battery |",
        ]

        return (
            f"## 🔌 Text Wiring Blueprint: {mcu_name} Robotics Platform\n\n"
            f"**Logic Voltage:** {mcu_voltage} | **Architecture:** Dual-Rail Power Topology with Common Ground\n\n"
            + "\n".join(table)
            + "\n\n"
            "### ⚠️ Critical Hardware Wiring Rules:\n"
            "1. **Never Power Motors from MCU 5V Pin:** The ATmega/ESP32 onboard regulator is rated for <500mA. Two DC motors draw 1.2A–2.5A at startup or stall, which will instantly trigger brownout resets or permanently damage the regulator.\n"
            "2. **Common Ground Connection:** The external battery pack GND must connect directly to the microcontroller GND. Without this shared ground, control signals lack a reference voltage and motors will jitter or fail to respond.\n"
            "3. **Motor Noise Suppression:** Solder a 0.1µF ceramic capacitor across the terminals of each DC motor to suppress high-frequency EMI noise from inductive motor brushes."
        )

    elif kind == "plant-monitor" or "plant" in lower_idea or "watering" in lower_idea or "soil" in lower_idea:
        is_esp32 = platform == "esp32"
        mcu_name = "ESP32 DevKit V1" if is_esp32 else "Arduino Uno R3"
        adc_pin = "GPIO 34 (ADC1 CH6)" if is_esp32 else "A0 (Analog In)"
        relay_pin = "GPIO 26" if is_esp32 else "D4"

        table = [
            "| Module / Subsystem | Module Pin | Controller / Supply Rail | Wire Type | Voltage & Signal Notes |",
            "|---|---|---|---|---|",
            f"| Capacitive Soil Sensor | AOUT (Analog Signal) | {mcu_name} {adc_pin} | Jumper (F-to-M) | 0–3.0V analog moisture reading (corrosion-free) |",
            f"| Capacitive Soil Sensor | VCC, GND | {mcu_name} 3.3V rail, GND | Jumper (F-to-M) | Power from 3.3V to ensure ADC compatibility |",
            f"| 5V Relay Module | IN (Control Input) | {mcu_name} {relay_pin} | Jumper (F-to-M) | Active LOW or HIGH digital relay trigger |",
            f"| 5V Relay Module | VCC, GND | {mcu_name} 5V rail, GND | Jumper (F-to-M) | Relay coil power (requires 5V supply) |",
            "| 5V Relay Module | COM (Common) | External 5V USB Adapter (+) | Stranded Wire | Isolated pump power line |",
            "| 5V Relay Module | NO (Normally Open)| Mini DC Submersible Pump (+) | Stranded Wire | Switched positive pump lead |",
            "| Mini Submersible Pump | Negative Lead (-) | External 5V USB Adapter (-) | Stranded Wire | Direct ground return to external adapter |",
            f"| Microcontroller Power | Micro USB / USB-C | Dedicated 5V USB Charger | USB Cable | Isolated clean supply for microcontroller |",
        ]

        return (
            f"## 🔌 Text Wiring Blueprint: {mcu_name} Automated Plant Irrigation\n\n"
            f"**Logic Voltage:** {'3.3V' if is_esp32 else '5V'} | **Architecture:** Optically Isolated Relay Power Isolation\n\n"
            + "\n".join(table)
            + "\n\n"
            "### ⚠️ Critical Hardware Wiring Rules:\n"
            "1. **Galvanic Isolation of Water Pump:** The water pump must NEVER share its positive power line with the microcontroller. Always feed the pump through the relay's COM/NO dry contacts using a dedicated external 5V USB adapter.\n"
            "2. **3.3V ADC Protection:** For ESP32, power the soil sensor from 3.3V (not 5V) to ensure analog output never exceeds the 3.3V ADC limit on GPIO 34.\n"
            "3. **Physical Water Separation:** Mount the electronics enclosure at least 30cm away and physically higher than the water reservoir to prevent accidental siphon backflow or splashing."
        )

    elif "relay" in lower_idea or "channel" in lower_idea:
        table = [
            "| Module / Subsystem | Module Pin | ESP32 Controller Pin | Wire Type | Voltage and Signal Notes |",
            "|---|---|---|---|---|",
            "| 4-Channel Relay Module | IN1 (Relay Channel 1) | ESP32 GPIO 25 | Jumper (F-to-M) | Digital Output trigger |",
            "| 4-Channel Relay Module | IN2 (Relay Channel 2) | ESP32 GPIO 26 | Jumper (F-to-M) | Digital Output trigger |",
            "| 4-Channel Relay Module | IN3 (Relay Channel 3) | ESP32 GPIO 27 | Jumper (F-to-M) | Digital Output trigger |",
            "| 4-Channel Relay Module | IN4 (Relay Channel 4) | ESP32 GPIO 32 | Jumper (F-to-M) | Digital Output trigger |",
            "| 4-Channel Relay Module | VCC, GND | External 5V Supply, GND | Jumper (F-to-M) | 5V Coil power (Do not draw from 3.3V!) |",
            "| 4-Channel Relay Module | JD-VCC / VCC Jumper | External 5V Supply | Jumper Cap | Optical isolation enabled |",
            "| HC-SR04 Ultrasonic Sensor | VCC, GND | External 5V Supply, GND | Jumper (F-to-M) | 5V Operating power |",
            "| HC-SR04 Ultrasonic Sensor | Trig (Trigger Pulse) | ESP32 GPIO 5 | Jumper (F-to-M) | 10us output pulse (3.3V TTL compatible) |",
            "| HC-SR04 Ultrasonic Sensor | Echo (Signal Return) | ESP32 GPIO 18 (via Divider) | 1k/2k Divider | MANDATORY: Step 5V Echo down to 3.3V |",
            "| Common Ground Bus | All GND Pins | ESP32 GND + External GND | Common Bus | Unify signal references |",
        ]
        return (
            "## Text Wiring Blueprint: ESP32 with 4-Channel Relay & HC-SR04\n\n"
            "**Architecture:** Opto-isolated relay switching with voltage-divided ultrasonic return.\n\n"
            + "\n".join(table)
            + "\n\n"
            "### Critical Electrical Protection:\n"
            "1. **Echo Voltage Divider:** HC-SR04 Echo pin outputs 5V. Insert a 1k resistor between Echo and GPIO 18, and a 2k resistor between GPIO 18 and GND to produce 3.33V safe input.\n"
            "2. **Relay JD-VCC Isolation:** Remove the JD-VCC jumper on the 4-channel relay board and power JD-VCC from external 5V to achieve complete galvanic isolation from ESP32 logic."
        )

    elif "bme280" in lower_idea or "weather" in lower_idea or "rain" in lower_idea:
        table = [
            "| Module / Subsystem | Module Pin | Raspberry Pi 4 Header Pin | Wire Type | Voltage and Protocol Notes |",
            "|---|---|---|---|---|",
            "| BME280 Sensor (Temp/Hum/Press) | VIN / VDD | Pin 1 (3.3V Power) | Jumper (F-to-F) | 3.3V Clean Power Rail |",
            "| BME280 Sensor (Temp/Hum/Press) | GND | Pin 6 (Ground) | Jumper (F-to-F) | System Ground |",
            "| BME280 Sensor (Temp/Hum/Press) | SCL (I2C Clock) | Pin 5 (GPIO 3 / SCL1) | Jumper (F-to-F) | I2C Bus 1 Clock (Onboard 1.8k pull-up) |",
            "| BME280 Sensor (Temp/Hum/Press) | SDA (I2C Data) | Pin 3 (GPIO 2 / SDA1) | Jumper (F-to-F) | I2C Bus 1 Data (Onboard 1.8k pull-up) |",
            "| Raindrop Sensor Comparator Module | VCC | Pin 17 (3.3V Power) | Jumper (F-to-F) | 3.3V Logic Power |",
            "| Raindrop Sensor Comparator Module | GND | Pin 9 (Ground) | Jumper (F-to-F) | System Ground |",
            "| Raindrop Sensor Comparator Module | D0 (Digital Out) | Pin 11 (GPIO 17 / BCM 17) | Jumper (F-to-F) | Active LOW rain detection interrupt |",
            "| Rain Sensing Nickel Board | Sensor Leads | LM393 Module Input | 2-wire cable | Variable resistance sensing surface |",
        ]
        return (
            "## Text Wiring Blueprint: Raspberry Pi 4 Weather Station (BME280 + Rain Sensor)\n\n"
            "**Protocol:** I2C Bus 1 (0x76 or 0x77) and GPIO Hardware Interrupt | **Logic:** 3.3V strictly\n\n"
            + "\n".join(table)
            + "\n\n"
            "### Raspberry Pi 4 Hardware Configuration:\n"
            "1. **Enable I2C:** Run `sudo raspi-config` -> Interface Options -> I2C -> Enable, then verify sensor address with `i2cdetect -y 1`.\n"
            "2. **3.3V Pure Logic:** Raspberry Pi GPIO pins have NO 5V TOLERANCE. Never power the LM393 rain sensor from 5V; power it exclusively from Pin 17 (3.3V)."
        )

    elif kind == "wearable-animatronic" or any(k in lower_idea for k in ("iron man", "suit", "animatronic", "wearable", "exoskeleton", "falcon", "captain america", "wings", "helmet")):
        mcu_name = "ESP32 DevKit V1" if platform == "esp32" else "Arduino Uno R3"
        sda_pin = "GPIO 21" if platform == "esp32" else "A4"
        scl_pin = "GPIO 22" if platform == "esp32" else "A5"
        led_pin = "GPIO 18" if platform == "esp32" else "D6"
        df_rx = "GPIO 16" if platform == "esp32" else "D10"
        df_tx = "GPIO 17" if platform == "esp32" else "D11"

        table = [
            "| Module / Subsystem | Module Pin | Controller / Supply Rail | Wire Type | Voltage & Signal Notes |",
            "|---|---|---|---|---|",
            f"| PCA9685 16-Ch PWM Driver | VCC, GND | {mcu_name} 5V rail, GND | Jumper (F-to-M) | Logic reference power |",
            f"| PCA9685 16-Ch PWM Driver | SDA, SCL | {mcu_name} {sda_pin}, {scl_pin} | Jumper (F-to-M) | I2C Bus control signal |",
            "| PCA9685 16-Ch PWM Driver | V+ (Servo Power) | LM2596 Buck Converter 5V/6V OUT (+) | 18 AWG Wire | High-current isolated servo power rail |",
            "| MG996R Servos (Visor / Wings) | PWM Signals | PCA9685 Channels 0 to 3 | 3-Pin Ribbon | Jitter-free multi-servo PWM control |",
            "| MG996R Servos (Visor / Wings) | Power Leads (+, -) | PCA9685 V+ & GND Rows | 3-Pin Ribbon | Powered directly from buck converter rail |",
            f"| WS2812B NeoPixel Ring/Strip | DIN (Data In) | {mcu_name} {led_pin} (via 470 Ohm) | Jumper (F-to-M) | High-speed addressable color signal |",
            "| WS2812B NeoPixel Ring/Strip | 5V (+), GND (-) | LM2596 5V OUT, Common GND | Stranded Wire | Separate high-current LED power tap |",
            f"| DFPlayer Mini Audio Module | VCC, GND | {mcu_name} 5V rail, GND | Jumper (F-to-M) | Audio module power |",
            f"| DFPlayer Mini Audio Module | RX (Audio Commands) | {mcu_name} {df_rx} (via 1k Ohm) | Jumper (F-to-M) | 1k Ohm resistor protects DFPlayer 3.3V UART |",
            f"| DFPlayer Mini Audio Module | TX (Status Return) | {mcu_name} {df_tx} | Jumper (F-to-M) | Serial status telemetry |",
            "| 8 Ohm 3W Speaker | SPK_1, SPK_2 | DFPlayer SPK Outputs | 22 AWG Wire | Differential DAC audio output |",
            f"| MPU-6050 Motion Sensor | SDA, SCL | {mcu_name} {sda_pin}, {scl_pin} | Jumper (F-to-M) | Shared I2C bus (Address 0x68) |",
            "| LM2596 Buck Converter | IN (+), IN (-) | External 7.4V-12V Battery Pack | 18 AWG Wire | Dedicated high-current battery power source |",
            f"| Common Star Ground Bus | Ground Rail | Battery (-) **AND** {mcu_name} GND | 18 AWG Wire | **MANDATORY COMMON GROUND** across all subsystems |",
        ]

        return (
            f"## 🔌 Text Wiring Blueprint: {mcu_name} Wearable Animatronics & Exoskeleton System\n\n"
            f"**Logic Voltage:** {'3.3V' if platform == 'esp32' else '5V'} | **Architecture:** Dual-Rail Isolated Power Topology with PCA9685 I2C Servo Buffer\n\n"
            + "\n".join(table)
            + "\n\n"
            "### ⚠️ Critical Wearable Hardware Wiring Rules:\n"
            "1. **Never Power Servos from MCU Pin:** Multiple MG996R servos draw 3A to 6A peak stall current. Connecting them to microcontroller 5V pin will permanently incinerate onboard linear voltage regulators and trigger continuous brownouts.\n"
            "2. **PCA9685 External V+ Input:** Feed regulated 5V to 6V from the LM2596 buck converter directly into the screw terminals of the PCA9685 board.\n"
            "3. **UART Resistor on DFPlayer:** The DFPlayer RX pin is sensitive; always place a 1k Ohm series resistor between controller TX and DFPlayer RX to suppress voltage spikes.\n"
            "4. **Decoupling Buffer:** Solder a 1000µF 16V electrolytic capacitor across the LM2596 output terminals to buffer inrush surges when motorized visor or wings deploy simultaneously."
        )

    else:
        table = [
            "| Module / Subsystem | Module Pin | Controller Pin | Wire Type | Voltage Notes |",
            "|---|---|---|---|---|",
            f"| Main Input Sensor | Signal / Out | Controller Signal Pin | Jumper Wire | Match logic voltage ({'3.3V' if platform == 'esp32' else '5V'}) |",
            f"| Main Input Sensor | VCC, GND | Controller 3.3V/5V, GND | Jumper Wire | Check sensor datasheet before applying power |",
            f"| Status Indicator | Digital Pin | Controller Free GPIO | Jumper Wire | Use 220 Ohm current limiting resistor with LED |",
            "| Microcontroller Power | USB Port | 5V USB Power Source | USB Cable | Clean regulated power |",
        ]
        return (
            f"## 🔌 Text Wiring Blueprint: {platform.title()} System\n\n"
            + "\n".join(table)
            + "\n\n"
            "### ⚠️ Hardware Guidelines:\n"
            "1. Verify component logic voltages before connecting signals.\n"
            "2. Establish common ground across all interconnected modules.\n"
            "3. Test individual sensor readings before assembling final enclosure."
        )


def simulate_failure(query: str, platform: str = "") -> str:
    """Run an engineering failure simulation analyzing physical hardware fault modes."""
    lower = query.lower()

    if any(k in lower for k in ("motor", "driver", "current", "l298n", "draws more", "stall", "brownout")):
        return (
            "## ⚡ Engineering Failure Simulation: Motor Driver Overcurrent & Controller Brownout\n\n"
            "### 1. Failure Scenario & Symptoms\n"
            "- **Observed Symptoms:** The microcontroller resets intermittently or reboots in an infinite loop whenever the motors start or turn. Sensor readings fluctuate wildly or return corrupted values, and motors experience stuttering.\n"
            "- **Fault Trigger:** DC gearmotors draw a high inrush stall current (1.5A to 2.5A per motor) upon startup, acceleration, or physical obstruction.\n\n"
            "### 2. Physical Root Cause Analysis\n"
            "- **Voltage Sag / Brownout:** Microcontroller boards (like Arduino Uno/Nano ATmega328P or ESP32) have an onboard low-dropout linear regulator (e.g. AMS1117) rated for a maximum of 500mA–800mA. When motor current is drawn through the controller's 5V pin, the regulator cannot supply the load, causing the 5V rail to collapse below 4.0V.\n"
            "- **BOD Reset:** The microcontroller's internal Brown-Out Detection (BOD) circuit detects the voltage dip below safe threshold and immediately triggers a hardware CPU reset.\n"
            "- **Inductive Voltage Spikes (Back-EMF):** Collapsing magnetic fields in motor windings generate high-voltage reverse transient spikes that penetrate logic lines without proper snubbing.\n\n"
            "### 3. Potential Consequences\n"
            "- Thermal destruction of the microcontroller's onboard voltage regulator.\n"
            "- Corrupted flash memory or EEPROM writes if brownout happens during storage write cycles.\n"
            "- Uncontrolled runaway behavior of the robot if the motor driver latch remains in an unknown state.\n\n"
            "### 4. Hardware Safeguards & Mitigation (The Fix)\n"
            "1. **Dual-Rail Power Architecture:** Power the L298N motor driver VMS pin directly from a separate battery pack (4×AA, 5×AA, or certified 2S Li-ion battery with BMS). Never tap motor supply from the Arduino 5V/VIN header.\n"
            "2. **Common Ground:** Tie the battery ground and microcontroller ground together at a single star-ground point.\n"
            "3. **Decoupling Capacitors:** Place a 100µF to 470µF electrolytic capacitor across the L298N power terminals to buffer motor surge currents, and a 0.1µF ceramic capacitor across motor leads to suppress brush arc noise.\n"
            "4. **Flyback Diodes:** Confirm the motor driver board has high-speed freewheeling diodes (the L298N module includes 8× 1N4007/FR107 diodes) to clamp inductive kickback."
        )

    elif any(k in lower for k in ("sensor wire", "comes loose", "disconnect", "loose", "soil moisture", "floating")):
        return (
            "## ⚡ Engineering Failure Simulation: Sensor Wire Disconnection / Open-Circuit Fault\n\n"
            "### 1. Failure Scenario & Symptoms\n"
            "- **Observed Symptoms:** The automated irrigation pump runs continuously without shutting off, completely draining the water reservoir and flooding the plant pots. Alternatively, the pump never turns on even when soil is visibly parched.\n"
            "- **Fault Trigger:** An analog signal jumper wire or power lead to the capacitive/resistive soil moisture sensor vibrates loose or disconnects.\n\n"
            "### 2. Physical Root Cause Analysis\n"
            "- **Floating ADC Input:** Microcontroller analog input pins (ATmega328P A0 or ESP32 GPIO 34) feature extremely high input impedance (>100M Ohm). When the sensor signal wire is severed, the pin floats with no pull-down/pull-up reference.\n"
            "- **False Moisture Interpretation:** Atmospheric electrostatic charges or internal leakage current drive the floating pin voltage to 0V or drift down to ground rail. The firmware interprets 0V as '0% moisture / bone-dry soil', triggering the irrigation pump loop indefinitely.\n\n"
            "### 3. Potential Consequences\n"
            "- Plant root rot and irreversible drowning damage.\n"
            "- Submersible water pump runs dry after depleting reservoir, leading to rotor seizure and burned-out motor windings.\n"
            "- Overflowing water poses a short-circuit and corrosion hazard to nearby low-voltage electronics.\n\n"
            "### 4. Hardware & Firmware Safeguards (The Fix)\n"
            "1. **Software Run-Time Watchdog:** Enforce a hard ceiling in firmware: `MAX_PUMP_RUN_SECONDS = 5`. The pump is killed immediately after 5 seconds regardless of sensor readings, with a mandatory 1-hour cooldown.\n"
            "2. **Sensor Sanity Bounds Check:** Legitimate capacitive sensors in air or water output between 1.2V and 2.8V (ADC raw values 300 to 900 on 10-bit). If the ADC reads <50 (disconnected to GND) or >1000 (disconnected to VCC), firmware flags a `HARDWARE_FAULT` and locks out the pump.\n"
            "3. **Physical Hardware Pull-Resistor:** Place a high-value resistor (100k Ohm) between the ADC pin and 3.3V/GND so an open circuit reliably pulls to an illegal fault code voltage."
        )

    elif any(k in lower for k in ("5v", "3.3v", "overvoltage", "level shifter", "logic level")):
        return (
            "## ⚡ Engineering Failure Simulation: 5V Logic Injection into 3.3V GPIO Rail\n\n"
            "### 1. Failure Scenario & Symptoms\n"
            "- **Observed Symptoms:** Microcontroller SoC (ESP32 or Raspberry Pi) becomes scalding hot to the touch. The specific GPIO pin stops detecting logic transitions, or the entire board enters an unbootable state with rapid current draw from the USB port.\n"
            "- **Fault Trigger:** Directly connecting a 5V sensor signal (such as HC-SR04 Echo pin or 5V Arduino output) to a 3.3V-only microcontroller GPIO pin.\n\n"
            "### 2. Physical Root Cause Analysis\n"
            "- **Internal Diode Conduction:** Modern 3.3V CMOS microcontrollers have internal ESD clamping diodes connected from each I/O pin to the internal 3.3V power rail (VDD). When 5V is applied, the upper diode becomes forward-biased (5V - 3.3V = 1.7V drop across diode).\n"
            "- **Current Injection & Latch-Up:** Large current (>15mA) rushes through the microscopic silicon diode structure into the 3.3V VDD rail. This triggers parasitic PNPN thyristor structures in CMOS silicon, creating a permanent short circuit between power and ground (silicon latch-up).\n\n"
            "### 3. Potential Consequences\n"
            "- Permanent destruction of the GPIO input pad and destruction of the SoC's internal analog/digital multiplexer.\n"
            "- Fire or scorching of the MCU surface; USB port brownout on host computer.\n\n"
            "### 4. Hardware Safeguards & Mitigation (The Fix)\n"
            "1. **Resistive Voltage Divider:** For unidirectional signals (e.g., Echo pin to ESP32), insert a 1k Ohm resistor between sensor out and GPIO, and a 2k Ohm resistor between GPIO and GND: $V_{out} = 5V \\times \\frac{2k}{1k + 2k} = 3.33V$.\n"
            "2. **Bi-Directional Logic Level Shifter:** For I2C/SPI bidirectional communication, use a dedicated BSS138 N-channel MOSFET level shifter module.\n"
            "3. **Power Sensor from 3.3V Rail:** Whenever possible, verify if the sensor supports 3.3V supply (e.g. RCWL-1601 or 3.3V-compatible HC-SR04P)."
        )

    elif any(k in lower for k in ("servo", "animatronic", "wearable", "wings", "suit", "pca9685", "helmet", "falcon", "captain america", "iron man")):
        return (
            "## ⚡ Engineering Failure Simulation: Multi-Servo Inrush Stall Current & Logic Brownout Reset\n\n"
            "### 1. Failure Scenario & Symptoms\n"
            "- **Observed Symptoms:** When wings deploy or helmet visor opens, the microcontroller resets in an infinite boot loop, WS2812B LEDs glitch or freeze on random colors, and servos shudder violently without completing their travel stroke.\n"
            "- **Fault Trigger:** Multiple high-torque servos (MG996R) actuate simultaneously from rest, drawing massive surge stall currents (up to 2.5A per motor).\n\n"
            "### 2. Physical Root Cause Analysis\n"
            "- **Transient Voltage Sag:** The initial mechanical inertia requires instantaneous rotor torque. Simultaneous startup of multiple servos pulls 4A to 8A for 50ms–150ms. If powered from a high internal-resistance battery or shared with microcontroller VCC, the 5V power bus collapses below the MCU's internal Brown-Out Detection (BOD) threshold (4.0V on ATmega328P, 2.8V on ESP32).\n"
            "- **Supply Rail Noise Injection:** Fast inductive switching of servo internal H-bridge MOSFETs injects high-frequency EMI noise (>100MHz transients) back through the ground return path, corrupting I2C clock (SCL) lines to the PCA9685.\n\n"
            "### 3. Potential Consequences\n"
            "- Total crash of central controller during wing expansion or flight posture.\n"
            "- Stripped nylon or metal servo gears due to un-damped oscillations and hunting.\n"
            "- Thermal overload of battery wiring harness and connector pins.\n\n"
            "### 4. Hardware Safeguards & Mitigation (The Fix)\n"
            "1. **Dedicated High-Current Buck Rail:** Step battery voltage down using an LM2596 or XL4015 buck converter rated for 5A+ continuous, feeding exclusively the PCA9685 V+ rail.\n"
            "2. **Bulk Low-ESR Decoupling Capacitor:** Place a 1000µF to 2200µF 16V electrolytic capacitor directly across the PCA9685 servo power terminal block to act as a local energy reservoir during inrush.\n"
            "3. **Firmware Staggered Servo Activation:** In software, never command all servos simultaneously at t=0. Introduce a 100ms phase offset between wing-left and wing-right actuation: actuate_left_wing(); delay(100); actuate_right_wing();.\n"
            "4. **Common Star-Ground:** Tie the logic ground and high-current power ground together at a single physical terminal point."
        )

    else:
        return (
            "## ⚡ Engineering Failure Simulation: Generic Subsystem Fault & Circuit Protection\n\n"
            "### 1. Failure Scenario & Symptoms\n"
            "- **Observed Symptoms:** Unexpected microcontroller reset, erratic input readings, or thermal buildup on power components.\n"
            "- **Fault Trigger:** Signal line degradation, supply noise, or unexpected load transients.\n\n"
            "### 2. Physical Root Cause Analysis\n"
            "- Inductive kickback, fluctuating battery discharge curves, or ground loop voltage differences create noise margins that exceed TTL/CMOS thresholds.\n\n"
            "### 3. Hardware & Firmware Safeguards\n"
            "1. **Star-Ground Topology:** Route power grounds and signal grounds separately, uniting them only at the power source.\n"
            "2. **Watchdog Timers:** Enable internal hardware watchdog timers (WDT) to safely reset firmware if execution hangs in a blocking loop.\n"
            "3. **Current Limiting:** Place current-limiting series resistors (220 Ohm–470 Ohm) on output pins driving LEDs or external base transistors."
        )


def render_detailed_timeline_and_tasks(request: ForgeRequest, plan: ForgePlan) -> str:
    """Generate a structured hackathon team timeline with per-member task allocations."""
    lower = request.idea.lower()
    team_size = max(1, min(request.team_size or 4, 6))

    roles = [
        (
            "Member 1: Hardware & Power Lead",
            [
                "Verify all received components against the verified BOM datasheet specifications.",
                "Assemble the dual-rail power distribution board (battery pack, L298N motor driver/relay isolation).",
                "Measure stall currents and confirm shared common ground wiring.",
                "Perform cold continuity checks with a multimeter before applying first power.",
            ],
        ),
        (
            "Member 2: Firmware & Navigation/Logic Lead",
            [
                "Set up the IDE toolchain, pin mapping header files, and board definitions.",
                "Implement low-level drivers (PWM motor control or relay switching routines).",
                "Develop the central state machine (sensor polling, threshold analysis, actuation loop).",
                "Implement firmware watchdogs, sensor range validation, and emergency failsafe timeouts.",
            ],
        ),
        (
            "Member 3: QA, Testing & Failure Mode Engineer",
            [
                "Execute the subsystem test matrix (sensor calibration, bench motor load test).",
                "Simulate physical failure modes (sensor disconnection, supply voltage dips, motor stalls).",
                "Log all observed issues, resolutions, and test completions in `output/vison-forge-build-pack/BUILD_JOURNAL.json`.",
                "Verify safety guidelines (no high voltages, temperature within safe thermal envelope).",
            ],
        ),
        (
            "Member 4: Documentation, BOM & Submission Lead",
            [
                "Maintain project documentation (`README.md`, `BOM.md`, `BUILD_PLAN.md`).",
                "Record high-resolution photos and video evidence of each verified subsystem.",
                "Produce the 3–5 minute hackathon demo video showing autonomous operation.",
                "Prepare the final hackathon presentation deck and complete the submission checklist.",
            ],
        ),
    ]

    assigned_roles = roles[:team_size]

    role_sections = []
    for title, tasks in assigned_roles:
        task_list = "\n".join(f"  - [ ] {t}" for t in tasks)
        role_sections.append(f"### 👤 {title}\n{task_list}")

    timeline_weeks = [
        (
            "Week 1: Architecture, BOM Procurement & Subsystem Bench Testing",
            [
                "Day 1–2: Confirm platform selection, finalize pinout allocations, order components via verified Quartz links.",
                "Day 3–4: Set up git repository, initialize build journal, configure firmware toolchain.",
                "Day 5–7: Bench test individual sensors and actuators in isolation on breadboard using USB power.",
            ],
        ),
        (
            "Week 2: Full Circuit Integration & Core Logic Implementation",
            [
                "Day 8–10: Assemble mechanical chassis/enclosure, wire dual-rail power topology with common ground.",
                "Day 11–12: Integrate firmware state machine with real-time sensor interrupts and actuation routines.",
                "Day 13–14: Conduct dry-run tests and measure current draw across all operational modes.",
            ],
        ),
        (
            "Week 3: Failure Stress Testing, Demo Video & Submission",
            [
                "Day 15–17: Run comprehensive failure simulations (wire disconnects, motor stall recovery, brownout resilience).",
                "Day 18–19: Record 3-minute hackathon demonstration video and compile benchmark telemetry.",
                "Day 20–21: Finalize README, verify submission checklist, tag git release, and submit to hackathon portal.",
            ],
        ),
    ]

    timeline_sections = []
    for week_title, days in timeline_weeks:
        day_lines = "\n".join(f"- **{d}**" for d in days)
        timeline_sections.append(f"### 📅 {week_title}\n{day_lines}")

    return (
        f"## 👥 Project Team Task Allocations ({team_size}-Person Team)\n\n"
        + "\n\n".join(role_sections)
        + "\n\n## 🗓️ 3-Week Hackathon Execution Timeline\n\n"
        + "\n\n".join(timeline_sections)
        + "\n\n### 📝 Milestone Journal Tracking Setup\n"
        "Your project progress is tracked in `output/vison-forge-build-pack/BUILD_JOURNAL.json`.\n"
        "As your team achieves milestones, send updates to Vison Forge (e.g.):\n"
        "- `completed: Sensor bench test passed and calibrated.`\n"
        "- `completed: Motor driver dual-power wiring verified without brownouts.`\n"
        "- `completed: Autonomous navigation demo recorded.`\n\n"
        "Vison Forge will timestamp each milestone and maintain your official audit trail."
    )


def render_detailed_bom(plan: ForgePlan, request: ForgeRequest | None = None) -> str:
    """Generate the structured Bill of Materials with live retailer links and tiers."""
    component_lines = [
        "| Component | Qty | Purpose | Verified Seller | Displayed Price | Stock | Buy Link | Checked |",
        "|---|---:|---|---|---:|---|---|---|",
    ]
    for item in plan.components:
        if item.selected_option:
            opt = item.selected_option
            stock = "In stock" if opt.in_stock is True else ("Out of stock" if opt.in_stock is False else "Unstated")
            component_lines.append(
                f"| {item.name} | {item.quantity} | {item.purpose} | {opt.seller} | ₹{opt.price:.2f} | {stock} | [Buy Option]({opt.url}) | {opt.checked_at} |"
            )
        else:
            component_lines.append(
                f"| {item.name} | {item.quantity} | {item.purpose} | — | Unavailable | — | — | {item.purchase_status} |"
            )
    bom_table = "\n".join(component_lines)

    tier_blocks = []
    if plan.tiers:
        tier_blocks.append("### 🏷️ Verified Build Options (Tiers)")
        for tier in plan.tiers:
            status_text = "All items verified" if tier.is_complete else "Partial estimate"
            tier_blocks.append(f"- **{tier.name} Tier (₹{tier.total_cost:.2f})**: {tier.description} ({status_text})")

    total_note = ""
    if plan.estimated_total is not None:
        total_note = f"\n**Estimated Project Total:** ₹{plan.estimated_total:.2f} {plan.total_currency}"
        if request and request.budget:
            diff = request.budget - plan.estimated_total
            if diff >= 0:
                total_note += f" *(Within ₹{request.budget:.0f} budget by ₹{diff:.2f})*"
            else:
                total_note += f" *(Exceeds ₹{request.budget:.0f} budget by ₹{-diff:.2f})*"

    disclaimer = plan.disclaimer or ComponentResearchService.DISCLAIMER

    return (
        "## 📦 Structured Bill of Materials (BOM)\n\n"
        + bom_table
        + "\n"
        + total_note
        + "\n\n"
        + "\n".join(tier_blocks)
        + f"\n\n> **Notice:** {disclaimer}"
    )
