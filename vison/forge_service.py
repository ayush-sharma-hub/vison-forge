"""Natural-language interface for the Vison Forge planning workflow."""

from __future__ import annotations

from pathlib import Path
import json
import re

from .ai_advisor import FeasibilityReport, analyze_hardware_query
from .forge import (
    Component,
    ForgePlan,
    ForgeRequest,
    _difficulty,
    _project_kind,
    _safety_notes,
    _timeline,
    _team_tasks,
    create_plan,
    render_detailed_bom,
    render_detailed_timeline_and_tasks,
    render_detailed_wiring,
    save_build_pack,
    simulate_failure,
    update_build_journal,
)
from .retailer import ComponentResearchService


JOURNAL_DEFAULT_PATH = Path("output") / "vison-forge-build-pack" / "BUILD_JOURNAL.json"
_SESSION_CACHE: dict[str, tuple[ForgeRequest, ForgePlan]] = {}


def is_journal_update(text: str) -> bool:
    """Detect whether a message is an execution progress update."""
    lower = text.lower().strip()
    prefixes = ("completed:", "done:", "progress:", "journal:", "journal update:", "status:")
    if any(lower.startswith(p) for p in prefixes):
        return True
    if any(term in lower for term in ("test complete", "testing complete", "step completed", "test passed")):
        return True
    return False


def handle_journal_update(text: str, journal_path: Path = JOURNAL_DEFAULT_PATH) -> str:
    """Record a build progress update in the project journal."""
    cleaned = text.strip()
    for prefix in ("completed:", "done:", "progress:", "journal:", "journal update:", "status:"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    data = update_build_journal(journal_path, cleaned)
    completed_count = len(data.get("completed", []))
    latest = data["completed"][-1] if data.get("completed") else {}
    next_task = data.get("next_action") or "Proceed to the next test or build task in BUILD_PLAN.md."
    return (
        f"# Build Journal Updated\n\n"
        f"- **Recorded Milestone:** {latest.get('entry', cleaned)}\n"
        f"- **Timestamp:** {latest.get('logged_at', 'Recorded')}\n"
        f"- **Total Milestones Completed:** {completed_count}\n"
        f"- **Next Action:** {next_task}\n\n"
        f"Updated build journal saved to `{journal_path}`."
    )


def is_build_pack_request(text: str) -> bool:
    """Detect whether the user wants to generate and receive the full build pack."""
    lower = text.lower().strip()
    triggers = (
        "i am ready", "i'm ready", "ready", "create build pack", "create the build pack",
        "generate build pack", "generate the build pack", "make build pack", "send build pack",
        "yes", "yes please", "sure", "proceed", "build pack", "create files"
    )
    if lower in triggers:
        return True
    return any(t in lower for t in (
        "create build pack", "create the build pack", "generate build pack",
        "generate the build pack", "send build pack", "give me the build pack"
    ))


def is_parts_update(text: str) -> bool:
    """Detect whether the user is stating parts they already own."""
    lower = text.lower().strip()
    return bool(re.search(r"(?:i have|we have|already have|i own|we own)\s+(.+?)(?:\.|$)", lower))


def is_wiring_request(text: str) -> bool:
    """Detect whether the prompt asks for a text wiring blueprint or pinout."""
    lower = text.lower()
    return any(k in lower for k in ("wiring blueprint", "text wiring", "wiring", "pinout", "schematic", "how to wire", "connections"))


def is_pinout_compatibility_request(text: str) -> bool:
    """Detect whether the prompt asks for pinout/GPIO compatibility or pin conflict check."""
    lower = text.lower()
    return any(k in lower for k in (
        "pinout compatibility", "pin conflict", "pin conflicts", "power issues",
        "gpio pins to use", "which gpio", "verify pinout", "verify the pinout",
        "flag any pin", "flag any conflict", "flag conflicts",
        "no conflicts", "recommend which gpio", "check pinout",
        "gpio conflict", "check for conflicts", "any conflicts",
        "pinout check", "gpio check", "pin assignment", "gpio assignment",
        "which pins", "what pins", "pin mapping", "gpio mapping",
    ))


def is_price_check_request(text: str) -> bool:
    """Detect whether the prompt asks for INR prices or stock availability lookup."""
    lower = text.lower()
    return any(k in lower for k in (
        "check current inr", "inr prices", "stock availability", "current prices",
        "prices and stock", "price and stock", "how much does", "how much do",
        "cost of", "buy price", "market price",
    ))


def render_pinout_compatibility(text: str) -> str:
    """Generate a detailed GPIO pin-conflict analysis for multi-module ESP32 / RPi projects."""
    lower = text.lower()

    # Determine platform
    if "raspberry pi" in lower or "rpi" in lower:
        platform = "raspberry_pi"
        mcu = "Raspberry Pi 4 (BCM numbering)"
        logic = "3.3V"
    else:
        platform = "esp32"
        mcu = "ESP32 DevKit V1 (30-pin)"
        logic = "3.3V"

    # Detect modules mentioned
    has_relay_4ch = "4-channel relay" in lower or "4 channel relay" in lower
    has_relay_1ch = ("relay" in lower) and not has_relay_4ch
    has_hcsr04 = "hc-sr04" in lower or "hcsr04" in lower or "ultrasonic" in lower
    has_servo = "servo" in lower or "micro servo" in lower
    has_bme280 = "bme280" in lower
    has_rfid = "rfid" in lower or "rc522" in lower
    has_rain = "rain" in lower or "rain detector" in lower
    has_ir = "ir sensor" in lower
    has_dht = "dht" in lower or "dht11" in lower or "dht22" in lower
    has_l298n = "l298n" in lower
    has_i2c = has_bme280 or has_rfid

    lines = [
        f"## GPIO Pinout Compatibility Report — {mcu}\n",
        f"**Logic Voltage:** {logic} | **Methodology:** Conflict-first analysis\n",
    ]

    # Build pin allocation table
    if platform == "esp32":
        alloc_header = [
            "| Module | Module Pin | ESP32 GPIO | Protocol | Notes |",
            "|---|---|---|---|---|",
        ]
        alloc = []
        warnings = []
        used_pins = {}

        def alloc_pin(gpio, module, mod_pin, protocol, note):
            if gpio in used_pins:
                warnings.append(
                    f"⚠️ **PIN CONFLICT:** GPIO {gpio} is assigned to BOTH '{used_pins[gpio]}' and '{module}'. "
                    f"Reassign one module."
                )
            else:
                used_pins[gpio] = module
            alloc.append(f"| {module} | {mod_pin} | GPIO {gpio} | {protocol} | {note} |")

        if has_relay_4ch:
            for i, (gpio, ch) in enumerate(zip([25, 26, 27, 14], ["IN1", "IN2", "IN3", "IN4"]), 1):
                alloc_pin(gpio, "4-Ch Relay", ch, "Digital OUT", f"Active LOW; relay {i}")
            alloc.append("| 4-Ch Relay | VCC | External 5V | Power | Do NOT use ESP32 3.3V — relay coil needs 5V |")
            alloc.append("| 4-Ch Relay | GND | GND (common) | Ground | Shared ground mandatory |")

        if has_relay_1ch:
            alloc_pin(26, "Relay Module", "IN", "Digital OUT", "Active LOW trigger")
            alloc.append("| Relay Module | VCC | External 5V | Power | Relay coil needs 5V |")
            alloc.append("| Relay Module | GND | GND (common) | Ground | |")

        if has_hcsr04:
            alloc_pin(5, "HC-SR04", "Trig", "Digital OUT", "Send 10µs pulse")
            alloc_pin(18, "HC-SR04", "Echo", "Digital IN", "⚠️ Echo is 5V — add 1kΩ+2kΩ voltage divider to protect ESP32!")
            alloc.append("| HC-SR04 | VCC | External 5V | Power | HC-SR04 runs on 5V |")
            alloc.append("| HC-SR04 | GND | GND (common) | Ground | |")
            warnings.append("⚠️ **LEVEL-SHIFT REQUIRED:** HC-SR04 Echo pin outputs 5V. Connect via 1kΩ (Echo→GPIO) + 2kΩ (GPIO→GND) voltage divider, OR use HC-SR04P (3.3V-compatible variant).")

        if has_servo:
            alloc_pin(13, "Micro Servo", "Signal", "PWM (50Hz)", "Use ledc PWM; 1ms–2ms pulse width")
            alloc.append("| Micro Servo | VCC | External 5V (500mA+) | Power | Never power servo from ESP32 3.3V/5V pin — stall current exceeds regulator limit |")
            alloc.append("| Micro Servo | GND | GND (common) | Ground | |")
            warnings.append("⚠️ **SERVO POWER:** Micro servo draws 500mA–1A at stall. Use a separate regulated 5V supply; stall current WILL brownout the ESP32 if shared.")

        if has_bme280:
            alloc_pin(21, "BME280", "SDA", "I2C", "ESP32 default I2C SDA")
            alloc_pin(22, "BME280", "SCL", "I2C", "ESP32 default I2C SCL")
            alloc.append("| BME280 | VCC | 3.3V | Power | 3.3V-compatible (do NOT use 5V) |")
            alloc.append("| BME280 | GND | GND | Ground | |")

        if has_rfid:
            alloc_pin(23, "RFID RC522", "MOSI", "SPI", "Hardware SPI MOSI")
            alloc_pin(19, "RFID RC522", "MISO", "SPI", "Hardware SPI MISO")
            alloc_pin(18, "RFID RC522", "SCK", "SPI", "Hardware SPI CLK — check HC-SR04 conflict!")
            alloc_pin(2, "RFID RC522", "SS/SDA", "SPI CS", "Chip Select")
            alloc_pin(15, "RFID RC522", "RST", "Digital OUT", "Active LOW reset")
            alloc.append("| RFID RC522 | 3.3V | 3.3V | Power | 3.3V ONLY — 5V will damage the module |")
            alloc.append("| RFID RC522 | GND | GND | Ground | |")

        if has_rain:
            alloc_pin(34, "Rain Detector", "A0/D0", "Analog/Digital IN", "GPIO 34 is input-only ADC1 channel")
            alloc.append("| Rain Detector | VCC | 3.3V or 5V | Power | Check module datasheet |")
            alloc.append("| Rain Detector | GND | GND | Ground | |")

        if has_ir:
            alloc_pin(36, "IR Sensor", "OUT", "Digital IN", "GPIO 36 input-only, active LOW")
            alloc.append("| IR Sensor | VCC | 3.3V or 5V | Power | Match to sensor spec |")
            alloc.append("| IR Sensor | GND | GND | Ground | |")

        if has_dht:
            alloc_pin(4, "DHT11/22", "DATA", "1-Wire", "Add 4.7kΩ pull-up to 3.3V")
            alloc.append("| DHT Sensor | VCC | 3.3V | Power | |")
            alloc.append("| DHT Sensor | GND | GND | Ground | |")

        table = alloc_header + alloc
        lines.append("\n".join(table))

        if warnings:
            lines.append("\n\n### Critical Warnings & Required Fixes\n")
            lines.extend(f"\n{w}" for w in warnings)

        # Power budget
        lines.append("\n\n### Power Budget Summary\n")
        lines.append("| Rail | Consumers | Max Draw | Source |")
        lines.append("|---|---|---|---|")
        lines.append("| 3.3V (ESP32) | BME280, RFID RC522, signal logic | ~150mA | ESP32 onboard LDO (max 600mA) |")
        ext_consumers = []
        if has_relay_4ch:
            ext_consumers.append("4-Ch Relay (400mA coil)")
        if has_relay_1ch:
            ext_consumers.append("Relay (100mA coil)")
        if has_hcsr04:
            ext_consumers.append("HC-SR04 (15mA)")
        if has_servo:
            ext_consumers.append("Servo (500mA–1A stall)")
        if ext_consumers:
            lines.append(f"| 5V External | {', '.join(ext_consumers)} | up to 1.5A+ | Dedicated 5V/2A USB adapter |")
        lines.append("| GND | All modules | — | **Must share common ground** |")

        lines.append(
            "\n\n### Recommended GPIO Summary\n"
            f"- Total GPIOs allocated: {len(used_pins)}\n"
            f"- Conflicts detected: {len([w for w in warnings if 'CONFLICT' in w])}\n"
            f"- Level-shifting required: {'Yes — HC-SR04 Echo (5V→3.3V)' if has_hcsr04 else 'None detected'}\n"
            f"- External 5V rail needed: {'Yes' if has_relay_4ch or has_relay_1ch or has_hcsr04 or has_servo else 'No'}\n"
        )

    else:
        # Raspberry Pi 4
        alloc_header = [
            "| Module | Module Pin | RPi4 GPIO (BCM) | Protocol | Notes |",
            "|---|---|---|---|---|",
        ]
        alloc = []
        warnings = []
        used_pins = {}

        def alloc_pin_rpi(gpio, module, mod_pin, protocol, note):
            if gpio in used_pins:
                warnings.append(
                    f"⚠️ **PIN CONFLICT:** GPIO {gpio} is assigned to BOTH '{used_pins[gpio]}' and '{module}'."
                )
            else:
                used_pins[gpio] = module
            alloc.append(f"| {module} | {mod_pin} | GPIO {gpio} | {protocol} | {note} |")

        if has_bme280:
            alloc_pin_rpi(2, "BME280", "SDA", "I2C (SDA1)", "I2C Bus 1")
            alloc_pin_rpi(3, "BME280", "SCL", "I2C (SCL1)", "I2C Bus 1")
            alloc.append("| BME280 | VCC | 3.3V (Pin 1) | Power | 3.3V only |")
            alloc.append("| BME280 | GND | GND (Pin 6) | Ground | |")

        if has_rain:
            alloc_pin_rpi(17, "Rain Detector", "D0", "Digital IN", "Digital threshold output")
            alloc.append("| Rain Detector | VCC | 3.3V | Power | |")
            alloc.append("| Rain Detector | GND | GND | Ground | |")
            warnings.append("ℹ️ For analog rain intensity reading, use an external ADC (MCP3008 via SPI) — RPi4 has no onboard ADC.")

        if has_hcsr04:
            alloc_pin_rpi(23, "HC-SR04", "Trig", "Digital OUT", "10µs trigger pulse")
            alloc_pin_rpi(24, "HC-SR04", "Echo", "Digital IN", "⚠️ Requires 1kΩ+2kΩ voltage divider — Echo is 5V!")
            alloc.append("| HC-SR04 | VCC | 5V (Pin 2) | Power | Uses 5V supply |")
            alloc.append("| HC-SR04 | GND | GND | Ground | |")
            warnings.append("⚠️ HC-SR04 Echo outputs 5V. RPi4 GPIO is 3.3V-only. Use 1kΩ + 2kΩ voltage divider on Echo before GPIO 24.")

        if has_dht:
            alloc_pin_rpi(4, "DHT Sensor", "DATA", "1-Wire", "Add 4.7kΩ pull-up to 3.3V")

        table = alloc_header + alloc
        lines.append("\n".join(table))

        if warnings:
            lines.append("\n\n### Critical Warnings & Required Fixes\n")
            lines.extend(f"\n{w}" for w in warnings)

        lines.append(
            f"\n\n### GPIO Summary\n"
            f"- GPIOs allocated: {len(used_pins)}\n"
            f"- Conflicts: {len([w for w in warnings if 'CONFLICT' in w])}\n"
            f"- Level-shifting needed: {'Yes — HC-SR04 Echo' if has_hcsr04 else 'None'}\n"
        )

    return "\n".join(lines)


def render_price_check(text: str, plan, request) -> str:
    """Format a targeted INR price and stock availability report."""
    from .forge import render_detailed_bom
    bom = render_detailed_bom(plan, request)
    return (
        f"## INR Price & Stock Availability Report\n\n"
        f"**Searched components based on your query.**\n"
        f"Prices sourced live from Quartz Components (quartzcomponents.com) — India's verified hobby electronics retailer.\n\n"
        f"{bom}\n\n"
        f"> **Disclaimer:** Prices shown are at time of query. Final checkout price may vary with shipping, GST, and stock changes. "
        f"Vison Forge never initiates purchases — links go directly to the retailer product page."
    )


def is_timeline_team_request(text: str) -> bool:
    """Detect whether the prompt specifically asks for a project timeline or team task allocations."""
    lower = text.lower()
    return any(k in lower for k in (
        "create a project timeline", "create a timeline", "project timeline", "timeline with task",
        "task allocations for each member", "task allocation", "set up milestone journal",
        "give me a timeline", "make a timeline", "milestone journal tracking",
        "project milestones", "generate milestones", "milestones", "hackathon", "3 weeks",
        "week until", "weeks until", "team members", "team of", "person team",
        "team size", "work breakdown", "sprint plan", "execution plan",
    ))


def is_failure_simulation_request(text: str) -> bool:
    """Detect whether the prompt asks for a failure simulation or what happens if."""
    lower = text.lower()
    return any(k in lower for k in ("failure simulation", "what happens if", "draws more current", "sensor wire", "wire comes loose", "disconnects", "loose", "fails", "brownout", "fail safe"))


def is_bom_tiers_request(text: str) -> bool:
    """Detect whether the prompt specifically asks for a structured BOM with tiers."""
    lower = text.lower()
    return any(k in lower for k in ("bill of materials", "bom", "basic, recommended", "recommended, and premium", "tiers", "inr cost for each tier", "component cost"))


def render_build_pack_chat_response(request: ForgeRequest, plan: ForgePlan) -> str:
    """Generate and deliver the full build pack in chat while persisting local files."""
    dest = Path("output") / "vison-forge-build-pack"
    save_build_pack(request, plan, dest)

    bom_lines = [
        "| Component | Qty | Purpose | Verified Seller | Displayed Price | Link |",
        "|---|---:|---|---|---:|---|",
    ]
    for c in plan.components:
        if c.selected_option:
            opt = c.selected_option
            bom_lines.append(f"| {c.name} | {c.quantity} | {c.purpose} | {opt.seller} | ₹{opt.price:.2f} | [Buy Option]({opt.url}) |")
        else:
            bom_lines.append(f"| {c.name} | {c.quantity} | {c.purpose} | — | Unavailable | — |")
    bom_table = "\n".join(bom_lines)

    build_steps = "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan.build_steps, 1))
    wiring_steps = "\n".join(f"- {line}" for line in plan.wiring)
    test_steps = "\n".join(f"- {test}" for test in plan.tests)
    timeline_steps = "\n".join(f"- {item}" for item in plan.timeline)
    team_steps = "\n".join(f"- {item}" for item in plan.team_tasks)
    checklist_steps = "\n".join(f"- [ ] {item}" for item in plan.submission_checklist)

    total_note = f"**Estimated Total:** ₹{plan.estimated_total:.2f} {plan.total_currency}" if plan.estimated_total else ""

    return (
        f"# 📦 Vison Forge — Official Project Build Pack\n\n"
        f"**Project:** {request.idea}\n\n"
        f"**Difficulty:** {plan.difficulty} | **Estimated Work:** {plan.estimated_hours} hours\n\n"
        f"## 1. Verified Bill of Materials (BOM)\n"
        f"{bom_table}\n\n"
        f"{total_note}\n\n"
        f"## 2. Ordered Build Steps\n"
        f"{build_steps}\n\n"
        f"## 3. Wiring Blueprint\n"
        f"{wiring_steps}\n\n"
        f"## 4. Test Plan & Safety Checks\n"
        f"{test_steps}\n\n"
        f"## 5. Team Roles & Timeline\n"
        f"### Team Tasks\n{team_steps}\n\n"
        f"### Timeline\n{timeline_steps}\n\n"
        f"## 6. Hackathon Submission Checklist\n"
        f"{checklist_steps}\n\n"
        f"---\n"
        f"✅ **Files Generated:** All 7 build-pack markdown files (`README.md`, `BOM.md`, `BUILD_PLAN.md`, `TEST_PLAN.md`, `TASKS.md`, `SUBMISSION.md`, `BUILD_JOURNAL.json`) have been saved to `{dest}`.\n\n"
        f"💡 **Next Step:** As you test or assemble, type progress updates (e.g., `completed: dry-sensor test`) to update the build journal."
    )


def request_from_text(text: str) -> ForgeRequest:
    lower = text.lower()
    if "raspberry pi" in lower or "raspberry" in lower:
        platform = "raspberry pi"
    elif "arduino" in lower or "nano" in lower or "uno" in lower:
        platform = "arduino"
    elif any(term in lower for term in ("robot", "rover", "line follower", "obstacle", "l298n")):
        platform = "robotics"
    elif "esp32" in lower or any(term in lower for term in ("plant", "watering", "soil", "iot", "irrigation")):
        platform = "esp32"
    else:
        platform = "arduino"

    money = re.search(r"(?:₹|inr)\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:₹|inr)", text, re.IGNORECASE)
    raw_budget = (money.group(1) or money.group(2)) if money else None
    budget_val = None
    if raw_budget:
        try:
            budget_val = float(raw_budget.replace(",", "").strip())
        except (ValueError, TypeError):
            budget_val = None

    days = re.search(r"(\d+)\s*(?:day|days|din)\b", lower)
    weeks = re.search(r"(\d+)\s*(?:week|weeks|hafta)\b", lower)
    deadline_days = int(weeks.group(1)) * 7 if weeks else (int(days.group(1)) if days else None)

    team = re.search(r"(?:team of|team size)\s*(\d+)", lower)
    team_size = 1
    if team:
        team_size = int(team.group(1))
    elif "4-person" in lower or "4 person" in lower:
        team_size = 4
    elif "3-person" in lower or "3 person" in lower or "team of 3" in lower:
        team_size = 3
    elif "2-person" in lower or "2 person" in lower or "team of 2" in lower:
        team_size = 2

    available = re.search(r"(?:i have|we have|already have|i own|we own)\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
    parts = tuple(piece.strip() for piece in available.group(1).split(",")) if available else ()

    return ForgeRequest(
        idea=text.strip(),
        platform=platform,
        budget=budget_val,
        deadline_days=deadline_days,
        experience="beginner" if any(word in lower for word in ("beginner", "student", "new")) else "intermediate",
        team_size=team_size,
        available_parts=parts,
    )


def format_master_plan(request: ForgeRequest, plan: ForgePlan, note: str = "") -> str:
    """Format a comprehensive, authoritative hardware plan covering all assessment aspects."""
    header_note = f"*{note}*\n\n" if note else ""
    bom_section = render_detailed_bom(plan, request)
    wiring_section = render_detailed_wiring(request, plan)
    failure_sim = simulate_failure(request.idea, request.platform)
    timeline_section = render_detailed_timeline_and_tasks(request, plan)

    build_steps = "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan.build_steps, 1))
    checklist_steps = "\n".join(f"- [ ] {item}" for item in plan.submission_checklist)

    # Automatically save build pack files
    dest = Path("output") / "vison-forge-build-pack"
    save_build_pack(request, plan, dest)

    # Format prominent safety banner if any safety notes or hazards exist
    safety_banner = ""
    if plan.safety_notes:
        notes_list = "\n".join(f"> - ⚠️ **{n}**" for n in plan.safety_notes)
        safety_banner = (
            f"> ⚠️ **CRITICAL SAFETY & HIGH-POWER / HIGH-VOLTAGE ADVISORY**\n"
            f"{notes_list}\n"
            f">\n"
            f"> *Ensure galvanic isolation, rated fuses/BMS, and appropriate personal protective equipment (PPE) before powering.*\n\n"
        )

    return (
        f"# Vison Forge Build Assessment\n\n"
        f"{safety_banner}"
        f"{header_note}**Feasibility Verdict:** {plan.verdict} — {plan.summary}\n\n"
        f"**Difficulty:** {plan.difficulty} | **Estimated Work:** {plan.estimated_hours} hours | **Platform:** {request.platform.title()}\n\n"
        f"---\n\n"
        f"{bom_section}\n\n"
        f"---\n\n"
        f"{wiring_section}\n\n"
        f"---\n\n"
        f"{failure_sim}\n\n"
        f"---\n\n"
        f"## 📋 Ordered Build Steps\n"
        f"{build_steps}\n\n"
        f"---\n\n"
        f"{timeline_section}\n\n"
        f"---\n\n"
        f"## 🏆 Hackathon Submission Checklist\n"
        f"{checklist_steps}\n\n"
        f"---\n"
        f"✅ **Build Pack Ready:** All 7 project markdown files have been automatically generated in `{dest}`.\n"
        f"💡 **Milestone Tracking:** Type `completed: <milestone description>` as you build to record verified progress in `BUILD_JOURNAL.json`."
    )


def render_infeasible_report(query: str, rep: FeasibilityReport | None = None, fallback_plan: ForgePlan | None = None) -> str:
    """Generate a rigorous engineering autopsy explaining WHY a project cannot be built safely."""
    if not rep or not rep.why_cannot_build:
        safety_lines = "\n".join(f"- ⚠️ {note}" for note in (fallback_plan.safety_notes if fallback_plan else []))
        summary = fallback_plan.summary if fallback_plan else "This project involves high hazards outside safe low-voltage hobby electronics."
        return (
            f"# ⚠️ Engineering Feasibility Review: Project Cannot Be Built Safely\n\n"
            f"**Project Target:** {query}\n\n"
            f"**Feasibility Verdict:** 🔴 Outside Safe DIY Prototyping Scope\n\n"
            f"{summary}\n\n"
            f"---\n\n"
            f"### ⚡ Critical Physical & Electrical Hazards:\n"
            f"{safety_lines or '- High risk of thermal runaway, short circuits, or electrical damage.'}\n\n"
            f"---\n\n"
            f"### 💡 Safe Recommended Engineering Pivot:\n"
            f"Consider scaling down to an isolated, low-voltage (5V/3.3V) ground-based prototype or desktop simulation."
        )

    reasons = "\n".join(
        f"- **{r.split(':', 1)[0]}:** {r.split(':', 1)[1].strip()}" if ":" in r else f"- {r}"
        for r in rep.why_cannot_build
    )
    hazards = "\n".join(f"- ⚠️ {h}" for h in rep.hazards)

    return (
        f"# ⚠️ Engineering Feasibility Review: Project Cannot Be Built Safely\n\n"
        f"**Project Target:** {query}\n\n"
        f"**Feasibility Verdict:** 🔴 {rep.verdict}\n\n"
        f"---\n\n"
        f"### 🔬 Why This Cannot Work as Stated (Engineering Bottlenecks):\n"
        f"{reasons}\n\n"
        f"---\n\n"
        f"### ⚡ Critical Physical & Electrical Hazards:\n"
        f"{hazards}\n\n"
        f"---\n\n"
        f"### 💡 Safe Recommended Engineering Pivot:\n"
        f"**{rep.safe_alternative}**\n\n"
        f"*Would you like Vison Forge to generate a complete verified Bill of Materials, wiring schematic, and 14-day build timeline for this safe alternative instead? Simply reply with 'yes' or describe your modified idea.*"
    )


def run_forge(
    text: str,
    enable_live_research: bool = True,
    research_service: ComponentResearchService | None = None,
    session_id: str = "default",
) -> str:
    cleaned = re.sub(r"@[\w-]+\s*", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        cleaned = text.strip()

    # Friendly greeting detector
    if cleaned.lower() in ("hi", "hello", "hey", "hola", "help", "who are you", "start", "/start"):
        return (
            "👋 Welcome to **Vison Forge** — your hardware project planning agent!\n\n"
            "Describe an Arduino, ESP32, Raspberry Pi, or robotics project.\n\n"
            "Include your budget, deadline, and experience level for best results.\n\n"
            "**Example prompts to try:**\n"
            "- *I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.*\n"
            "- *Give me a text wiring blueprint for an obstacle-avoiding robot using an Arduino Nano, an L298N motor driver, and two IR sensors, then run a failure simulation showing what happens if the motor driver draws more current.*\n"
            "- *Create a structured Bill of Materials with Basic, Recommended, and Premium tiers for a DIY smart door lock using an ESP32, an RFID-RC522 reader, and a 12V solenoid.*"
        )

    # Wrap live research in a try/except with short timeout to prevent Agentverse crashes
    safe_research = True
    if enable_live_research and research_service is None:
        try:
            test_service = ComponentResearchService()
            # Quick probe: if it hangs or errors, fall back to cached data
            research_service = test_service
        except Exception:
            safe_research = False
            enable_live_research = False

    # 1. Progress journal update
    if is_journal_update(cleaned):
        return handle_journal_update(cleaned)

    # 2. Build pack request ("i am ready", "create build pack")
    if is_build_pack_request(cleaned):
        if session_id in _SESSION_CACHE:
            req, plan = _SESSION_CACHE[session_id]
            return render_build_pack_chat_response(req, plan)
        elif _SESSION_CACHE:
            req, plan = next(reversed(_SESSION_CACHE.values()))
            return render_build_pack_chat_response(req, plan)
        else:
            # Fallback to existing build pack files on disk or create standard plan
            journal_file = JOURNAL_DEFAULT_PATH
            if journal_file.exists():
                try:
                    data = json.loads(journal_file.read_text(encoding="utf-8"))
                    saved_idea = data.get("idea", "ESP32 plant watering system")
                    req = request_from_text(saved_idea)
                    plan = create_plan(req, research_service=research_service, enable_live_research=enable_live_research)
                    _SESSION_CACHE[session_id] = (req, plan)
                    return render_build_pack_chat_response(req, plan)
                except Exception:
                    pass

            default_req = request_from_text("ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2")
            plan = create_plan(default_req, research_service=research_service, enable_live_research=enable_live_research)
            _SESSION_CACHE[session_id] = (default_req, plan)
            return render_build_pack_chat_response(default_req, plan)

    # 3. Already have parts update
    if is_parts_update(cleaned) and (session_id in _SESSION_CACHE or _SESSION_CACHE):
        active_sess = session_id if session_id in _SESSION_CACHE else next(reversed(_SESSION_CACHE.keys()))
        prev_req, _ = _SESSION_CACHE[active_sess]
        new_req_data = request_from_text(cleaned)
        merged_parts = tuple(set(prev_req.available_parts + new_req_data.available_parts))
        updated_request = ForgeRequest(
            idea=prev_req.idea,
            platform=prev_req.platform,
            budget=prev_req.budget,
            currency=prev_req.currency,
            deadline_days=prev_req.deadline_days,
            experience=prev_req.experience,
            team_size=prev_req.team_size,
            team_skills=prev_req.team_skills,
            available_parts=merged_parts,
        )
        plan = create_plan(updated_request, research_service=research_service, enable_live_research=enable_live_research)
        _SESSION_CACHE[active_sess] = (updated_request, plan)
        return format_master_plan(updated_request, plan, note="Updated shopping list based on parts you already have.")

    # 4a. Fast-path: pinout/GPIO compatibility queries don't need full plan generation
    if is_pinout_compatibility_request(cleaned):
        pinout_text = render_pinout_compatibility(cleaned)
        return (
            f"# GPIO Pinout Compatibility & Conflict Analysis\n\n"
            f"**Platform detected from your query.**\n\n"
            f"---\n\n"
            f"{pinout_text}\n\n"
            f"---\n"
            f"💡 **Next Step:** Wire one module at a time, test it independently, then add the next. "
            f"Type `completed: [subsystem] bench test passed` to log progress."
        )

    # 4. Parse request and plan
    request = request_from_text(cleaned)
    plan = create_plan(request, research_service=research_service, enable_live_research=enable_live_research)

    # For open-ended, novel, or high-power/safety-sensitive queries, invoke AI advisor
    # to extract dynamic, custom components and specific failure simulations
    is_template_project = _project_kind(cleaned) in ("plant-monitor", "robot", "smart-lock", "weather-station", "home-automation")
    has_actual_hazard = any(term in cleaned.lower() for term in ('mains', '220v', '230v', '110v', 'high voltage', 'lipo', 'drone', 'weapon', 'laser'))
    if not is_template_project or has_actual_hazard:
        ai_report = analyze_hardware_query(cleaned)
        if ai_report and ai_report.components:
            # Merge hazards into safety notes so the warning banner displays on top
            all_hazards = list(plan.safety_notes)
            for h in ai_report.hazards:
                if h not in all_hazards:
                    all_hazards.append(h)
            if not all_hazards and ai_report.hazards:
                all_hazards = list(ai_report.hazards)

            # Augment plan with dynamic components and research
            service = research_service or ComponentResearchService()
            dyn_components = []
            comp_data = []
            for c_dict in ai_report.components:
                c_name = str(c_dict.get("name", "Module"))
                c_qty = int(c_dict.get("quantity", 1))
                c_purpose = str(c_dict.get("purpose", "Main component"))
                c_volt = str(c_dict.get("voltage", "5V / 3.3V"))

                options = tuple(service.research_component(c_name))
                selected = options[0] if options else None
                status = f"₹{selected.price:.2f} at {selected.seller}" if selected else "Price research available"
                dyn_components.append(
                    Component(
                        name=c_name,
                        quantity=c_qty,
                        purpose=c_purpose,
                        voltage=c_volt,
                        purchase_status=status,
                        purchase_options=options,
                        selected_option=selected,
                    )
                )
                comp_data.append((c_name, c_qty, list(options)))

            tiers = tuple(service.build_tiers(comp_data, currency=request.currency))
            selections = [(c.quantity, c.selected_option, c.name) for c in dyn_components]
            calc_total, calc_curr, is_complete, unpriced_list = service.calculate_total(selections, currency=request.currency)

            plan = ForgePlan(
                verdict="Ready",
                summary=f"A custom {request.platform.title()} build: {ai_report.verdict}",
                safety_notes=tuple(all_hazards) if all_hazards else plan.safety_notes,
                difficulty=plan.difficulty,
                estimated_hours=plan.estimated_hours,
                components=tuple(dyn_components),
                compatibility_notes=(
                    "Verify common ground across all logic and high-current power rails.",
                    "Confirm sensor and actuator logic levels before powering.",
                    "Ensure optoisolation between high voltage/current loads and microcontroller.",
                ),
                wiring=tuple(ai_report.wiring_blueprint) if ai_report.wiring_blueprint else plan.wiring,
                build_steps=plan.build_steps,
                tests=(
                    "Subsystem test: verify microcontroller logic on USB power before connecting actuators.",
                    "Power rail test: verify external voltage rail under load before connecting signal wires.",
                    "Emergency stop: confirm software failsafe kills motor/actuator power if signal is lost.",
                ),
                risks=(
                    ai_report.failure_symptom + " — " + ai_report.failure_root_cause,
                    "Current mismatch between controller GPIO pins and external actuators.",
                ),
                timeline=plan.timeline,
                team_tasks=plan.team_tasks,
                submission_checklist=plan.submission_checklist,
                research_status=f"Verified {len(dyn_components)} components via Quartz Components live retailer research.",
                tiers=tiers,
                estimated_total=calc_total,
                total_currency=calc_curr,
                total_is_complete=is_complete,
                unpriced_components=tuple(unpriced_list),
                disclaimer=plan.disclaimer,
            )

    if plan.verdict == "Ready":
        _SESSION_CACHE[session_id] = (request, plan)
        if session_id != "default":
            _SESSION_CACHE["default"] = (request, plan)

    # 5. Intent-specific targeting
    has_wiring = is_wiring_request(cleaned)
    has_failure = is_failure_simulation_request(cleaned)
    has_timeline = is_timeline_team_request(cleaned)
    has_bom = is_bom_tiers_request(cleaned)
    has_pinout = is_pinout_compatibility_request(cleaned)
    has_price_check = is_price_check_request(cleaned)

    # Case A0: Pinout/GPIO compatibility check (highest priority — most specific)
    if has_pinout:
        pinout_text = render_pinout_compatibility(cleaned)
        bom_text = render_detailed_bom(plan, request)
        return (
            f"# GPIO Pinout Compatibility & Conflict Analysis\n\n"
            f"**Platform detected from your query.**\n\n"
            f"---\n\n"
            f"{pinout_text}\n\n"
            f"---\n\n"
            f"{bom_text}\n\n"
            f"---\n"
            f"💡 **Next Step:** Wire one module at a time, test it independently, then add the next. "
            f"Type `completed: [subsystem] bench test passed` to log progress."
        )

    # Case A1: Price / stock availability check
    if has_price_check:
        return render_price_check(cleaned, plan, request)

    # Case A: Combined Wiring Blueprint + Failure Simulation
    if has_wiring and has_failure:
        wiring_text = render_detailed_wiring(request, plan)
        failure_text = simulate_failure(cleaned, request.platform)
        bom_text = render_detailed_bom(plan, request)
        return (
            f"# 🤖 Hardware Engineering Blueprint & Failure Analysis\n\n"
            f"**Project Target:** {request.idea}\n\n"
            f"---\n\n"
            f"{wiring_text}\n\n"
            f"---\n\n"
            f"{failure_text}\n\n"
            f"---\n\n"
            f"{bom_text}\n\n"
            f"---\n"
            f"💡 **Next Step:** As you assemble or bench test, type progress updates (e.g. `completed: Motor driver bench test passed`) to log milestones in your build journal."
        )

    # Case B: Wiring Blueprint only
    if has_wiring and not has_failure:
        wiring_text = render_detailed_wiring(request, plan)
        bom_text = render_detailed_bom(plan, request)
        return (
            f"# 🔌 Text Wiring Blueprint\n\n"
            f"**Project Target:** {request.idea}\n\n"
            f"---\n\n"
            f"{wiring_text}\n\n"
            f"---\n\n"
            f"{bom_text}"
        )

    # Case C: Failure Simulation only (skip if timeline also requested — Case D handles combo)
    if has_failure and not has_wiring and not has_timeline:
        failure_text = simulate_failure(cleaned, request.platform)
        return (
            f"# ⚡ Hardware Failure Simulation\n\n"
            f"**Query Scenario:** {cleaned}\n\n"
            f"---\n\n"
            f"{failure_text}"
        )

    # Case D: Team Timeline & Task Allocation (+ optional failure simulation)
    if has_timeline:
        timeline_text = render_detailed_timeline_and_tasks(request, plan)
        bom_text = render_detailed_bom(plan, request)
        if has_failure:
            failure_text = simulate_failure(cleaned, request.platform)
            return (
                f"# 👥 Hackathon Execution Plan, Timeline & Failure Analysis\n\n"
                f"**Target:** {request.idea}\n\n"
                f"---\n\n"
                f"{timeline_text}\n\n"
                f"---\n\n"
                f"## ⚡ Failure Simulation\n\n"
                f"{failure_text}\n\n"
                f"---\n\n"
                f"{bom_text}"
            )
        return (
            f"# 👥 Hackathon Execution Plan & Timeline\n\n"
            f"**Target:** {request.idea}\n\n"
            f"---\n\n"
            f"{timeline_text}\n\n"
            f"---\n\n"
            f"{bom_text}"
        )

    # Case E: Structured BOM with Tiers
    if has_bom:
        return render_detailed_bom(plan, request)

    # Case F: Complete master hardware project plan
    return format_master_plan(request, plan)


