"""Local command-line entry point for Vison Forge."""

from __future__ import annotations

from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from vison.forge import create_plan, save_build_pack
from vison.forge_service import request_from_text, run_forge


def main() -> None:
    print("Vison Forge — hardware project planning agent")
    print("Describe a low-voltage Arduino, ESP32, Raspberry Pi, or simple robotics project.")
    idea = input("\nProject idea: ").strip()
    if not idea:
        print("Please describe the project, platform, budget, deadline, and experience level.")
        return
    print()
    print(run_forge(idea))
    should_save = input("\nCreate the local build-pack files now? (y/N): ").strip().lower()
    if should_save not in {"y", "yes"}:
        return
    request = request_from_text(idea)
    plan = create_plan(request, enable_live_research=True)
    if plan.verdict != "Ready":
        print("No files were created because this plan needs clarification or is outside the safe MVP scope.")
        return
    destination = Path("output") / "vison-forge-build-pack"
    paths = save_build_pack(request, plan, destination)
    print("\nCreated:")
    for path in paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()

