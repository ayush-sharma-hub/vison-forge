"""Natural-language interface for the Vison Forge planning workflow."""

from __future__ import annotations

from pathlib import Path
import re

from .forge import ForgeRequest, create_plan, update_build_journal
from .retailer import ComponentResearchService


JOURNAL_DEFAULT_PATH = Path("output") / "vison-forge-build-pack" / "BUILD_JOURNAL.json"


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


def request_from_text(text: str) -> ForgeRequest:
    lower = text.lower()
    if "raspberry pi" in lower:
        platform = "raspberry pi"
    elif "arduino" in lower:
        platform = "arduino"
    elif any(term in lower for term in ("robot", "rover", "line follower", "obstacle")):
        platform = "robotics"
    else:
        platform = "esp32" if "esp32" in lower else ""
    money = re.search(r"(?:₹|inr\s*)([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    days = re.search(r"(\d+)\s*(?:day|days|din)\b", lower)
    team = re.search(r"(?:team of|team size)\s*(\d+)", lower)
    available = re.search(r"(?:i have|we have|already have)\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
    parts = tuple(piece.strip() for piece in available.group(1).split(",")) if available else ()
    return ForgeRequest(
        idea=text.strip(), platform=platform,
        budget=float(money.group(1).replace(",", "")) if money else None,
        deadline_days=int(days.group(1)) if days else None,
        experience="beginner" if any(word in lower for word in ("beginner", "student", "new")) else "intermediate",
        team_size=int(team.group(1)) if team else 1,
        available_parts=parts,
    )


def run_forge(
    text: str,
    enable_live_research: bool = True,
    research_service: ComponentResearchService | None = None,
) -> str:
    if is_journal_update(text):
        return handle_journal_update(text)

    request = request_from_text(text)
    plan = create_plan(request, research_service=research_service, enable_live_research=enable_live_research)
    if plan.verdict != "Ready":
        return f"**{plan.verdict}**\n\n{plan.summary}\n\n" + "\n".join(f"- {note}" for note in plan.safety_notes)

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

    return (
        f"# Vison Forge Build Assessment\n\n**{plan.verdict}:** {plan.summary}\n\n"
        f"**Difficulty:** {plan.difficulty}\n\n**Estimated hands-on work:** {plan.estimated_hours} hours\n\n"
        f"## Components & Verified Purchase Options\n{components_text}\n{total_text}{tiers_text}\n"
        f"## First build task\n{plan.build_steps[0]}\n\n"
        f"## Purchase Research\n{plan.research_status}\n\n"
        f"{disclaimer_text}"
        "Ask me to create the build pack when you are ready; it includes README, BOM, wiring, tests, timeline, tasks, and submission checklist."
    )
