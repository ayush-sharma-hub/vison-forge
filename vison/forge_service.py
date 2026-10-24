"""Natural-language interface for the Vison Forge planning workflow."""

from __future__ import annotations

from pathlib import Path
import json
import re

from .forge import (
    ForgePlan,
    ForgeRequest,
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


def is_failure_simulation_request(text: str) -> bool:
    """Detect whether the prompt asks for a failure simulation or what happens if."""
    lower = text.lower()
    return any(k in lower for k in ("failure simulation", "what happens if", "draws more current", "sensor wire", "wire comes loose", "disconnects", "loose", "fails", "brownout", "fail safe"))


def is_timeline_team_request(text: str) -> bool:
    """Detect whether the prompt specifically asks for a project timeline or team task allocations."""
    lower = text.lower()
    return any(k in lower for k in (
        "create a project timeline", "create a timeline", "project timeline", "timeline with task",
        "task allocations for each member", "task allocation", "set up milestone journal",
        "give me a timeline", "make a timeline", "milestone journal tracking"
    ))


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

    money = re.search(r"(?:₹|inr\s*)([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
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
        budget=float(money.group(1).replace(",", "")) if money else None,
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

    return (
        f"# Vison Forge Build Assessment\n\n"
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


def run_forge(
    text: str,
    enable_live_research: bool = True,
    research_service: ComponentResearchService | None = None,
    session_id: str = "default",
) -> str:
    cleaned = re.sub(r"@agent1[a-z0-9]+\s*", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        cleaned = text.strip()

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

    # 4. Parse request and plan
    request = request_from_text(cleaned)
    plan = create_plan(request, research_service=research_service, enable_live_research=enable_live_research)
    if plan.verdict == "Ready":
        _SESSION_CACHE[session_id] = (request, plan)
        if session_id != "default":
            _SESSION_CACHE["default"] = (request, plan)

    if plan.verdict != "Ready":
        return f"**{plan.verdict}**\n\n{plan.summary}\n\n" + "\n".join(f"- {note}" for note in plan.safety_notes)

    # 5. Intent-specific targeting
    has_wiring = is_wiring_request(cleaned)
    has_failure = is_failure_simulation_request(cleaned)
    has_timeline = is_timeline_team_request(cleaned)
    has_bom = is_bom_tiers_request(cleaned)

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

    # Case C: Failure Simulation only
    if has_failure and not has_wiring:
        failure_text = simulate_failure(cleaned, request.platform)
        return (
            f"# ⚡ Hardware Failure Simulation\n\n"
            f"**Query Scenario:** {cleaned}\n\n"
            f"---\n\n"
            f"{failure_text}"
        )

    # Case D: Team Timeline & Task Allocation
    if has_timeline:
        timeline_text = render_detailed_timeline_and_tasks(request, plan)
        bom_text = render_detailed_bom(plan, request)
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
