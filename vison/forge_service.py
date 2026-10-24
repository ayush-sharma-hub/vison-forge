"""Natural-language interface for the Vison Forge planning workflow."""

from __future__ import annotations

from pathlib import Path
import re

from .forge import ForgePlan, ForgeRequest, create_plan, save_build_pack, update_build_journal
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
    if "raspberry pi" in lower:
        platform = "raspberry pi"
    elif "arduino" in lower:
        platform = "arduino"
    elif any(term in lower for term in ("robot", "rover", "line follower", "obstacle")):
        platform = "robotics"
    elif "esp32" in lower:
        platform = "esp32"
    elif any(term in lower for term in ("plant", "watering", "soil", "iot")):
        platform = "esp32"
    else:
        platform = ""

    money = re.search(r"(?:₹|inr\s*)([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    days = re.search(r"(\d+)\s*(?:day|days|din)\b", lower)
    team = re.search(r"(?:team of|team size)\s*(\d+)", lower)
    available = re.search(r"(?:i have|we have|already have|i own|we own)\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
    parts = tuple(piece.strip() for piece in available.group(1).split(",")) if available else ()
    return ForgeRequest(
        idea=text.strip(), platform=platform,
        budget=float(money.group(1).replace(",", "")) if money else None,
        deadline_days=int(days.group(1)) if days else None,
        experience="beginner" if any(word in lower for word in ("beginner", "student", "new")) else "intermediate",
        team_size=int(team.group(1)) if team else 1,
        available_parts=parts,
    )


def format_assessment(request: ForgeRequest, plan: ForgePlan, note: str = "") -> str:
    component_lines = []
    for item in plan.components:
        if item.selected_option:
            opt = item.selected_option
            stock_str = "in stock" if opt.in_stock is True else ("out of stock" if opt.in_stock is False else "stock unstated")
            component_lines.append(
                f"- {item.quantity}× {item.name}: ₹{opt.price:.2f} each ({opt.seller}, {stock_str}) — [Buy Link]({opt.url})"
            )
        else:
            component_lines.append(f"- {item.quantity}× {item.name}: {item.purpose} ({item.purchase_status})")
    components_text = "\n".join(component_lines)

    total_text = ""
    if plan.estimated_total is not None and plan.estimated_total > 0:
        status_note = "" if plan.total_is_complete else f" (partial estimate; unpriced: {', '.join(plan.unpriced_components)})"
        budget_note = ""
        if request.budget:
            diff = request.budget - plan.estimated_total
            if diff >= 0:
                budget_note = f" (within your ₹{request.budget:.0f} budget by ₹{diff:.2f})"
            else:
                budget_note = f" (exceeds your ₹{request.budget:.0f} budget by ₹{-diff:.2f})"
        total_text = f"\n**Estimated Total:** ₹{plan.estimated_total:.2f}{status_note}{budget_note}\n"

    tiers_text = ""
    if plan.tiers:
        tier_lines = ["\n### Build options"]
        for tier in plan.tiers:
            comp_str = "" if tier.is_complete else " (partial)"
            tier_lines.append(f"- **{tier.name}**: ₹{tier.total_cost:.2f}{comp_str} — {tier.description}")
        tiers_text = "\n".join(tier_lines) + "\n"

    disclaimer_text = f"> {plan.disclaimer}\n\n" if plan.disclaimer else ""
    header_note = f"*{note}*\n\n" if note else ""

    return (
        f"# Vison Forge Build Assessment\n\n{header_note}**{plan.verdict}:** {plan.summary}\n\n"
        f"**Difficulty:** {plan.difficulty}\n\n**Estimated hands-on work:** {plan.estimated_hours} hours\n\n"
        f"## Components & Verified Purchase Options\n{components_text}\n{total_text}{tiers_text}\n"
        f"## First build task\n{plan.build_steps[0]}\n\n"
        f"## Purchase Research\n{plan.research_status}\n\n"
        f"{disclaimer_text}"
        "Ask me to create the build pack when you are ready; it includes README, BOM, wiring, tests, timeline, tasks, and submission checklist."
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
            return (
                "No active project plan found in session memory. "
                "Please describe your project first (e.g., *'I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days'*), and I will create the full plan and BOM for you!"
            )

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
        return format_assessment(updated_request, plan, note="Updated shopping list based on parts you already have.")

    # 4. Standard planning request
    request = request_from_text(cleaned)
    if not request.platform and (session_id in _SESSION_CACHE or _SESSION_CACHE):
        active_sess = session_id if session_id in _SESSION_CACHE else next(reversed(_SESSION_CACHE.keys()))
        prev_req, _ = _SESSION_CACHE[active_sess]
        request = ForgeRequest(
            idea=cleaned,
            platform=prev_req.platform,
            budget=request.budget or prev_req.budget,
            currency=request.currency or prev_req.currency,
            deadline_days=request.deadline_days or prev_req.deadline_days,
            experience=request.experience or prev_req.experience,
            team_size=request.team_size or prev_req.team_size,
            available_parts=prev_req.available_parts,
        )

    plan = create_plan(request, research_service=research_service, enable_live_research=enable_live_research)
    if plan.verdict == "Ready":
        _SESSION_CACHE[session_id] = (request, plan)
        if session_id != "default":
            _SESSION_CACHE["default"] = (request, plan)

    if plan.verdict != "Ready":
        return f"**{plan.verdict}**\n\n{plan.summary}\n\n" + "\n".join(f"- {note}" for note in plan.safety_notes)

    return format_assessment(request, plan)
