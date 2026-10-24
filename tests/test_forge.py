from pathlib import Path
import tempfile
import unittest

from vison.forge import ForgeRequest, create_plan, save_build_pack
from vison.forge_service import request_from_text, run_forge


class ForgeTests(unittest.TestCase):
    def test_plant_project_creates_a_safe_plan(self):
        request = ForgeRequest(
            idea="Build an ESP32 plant watering system for two plants",
            platform="esp32",
            budget=2500,
            deadline_days=7,
            team_size=2,
        )
        plan = create_plan(request)
        self.assertEqual(plan.verdict, "Ready")
        self.assertTrue(any("pump" in item.name.lower() for item in plan.components))
        self.assertTrue(any("low-voltage" in note.lower() for note in plan.safety_notes))

    def test_mains_request_is_scaled_down(self):
        request = ForgeRequest(idea="Build a 220V Arduino watering system", platform="arduino")
        plan = create_plan(request)
        self.assertEqual(plan.verdict, "Scale down")
        self.assertIn("Mains electricity", plan.summary)

    def test_build_pack_creates_expected_artifacts(self):
        request = ForgeRequest(idea="ESP32 soil monitor", platform="esp32")
        plan = create_plan(request)
        with tempfile.TemporaryDirectory() as directory:
            paths = save_build_pack(request, plan, Path(directory))
            self.assertTrue(any(path.name == "README.md" for path in paths))
            self.assertTrue((Path(directory) / "BUILD_JOURNAL.json").exists())

    def test_run_forge_natural_language_output(self):
        text = "I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2."
        output = run_forge(text, enable_live_research=False)
        self.assertIn("Vison Forge Build Assessment", output)
        self.assertIn("Ready", output)
        self.assertIn("ESP32", output)
        self.assertIn("Notice:", output)

    def test_already_have_parts_omits_owned_from_bom(self):
        request = ForgeRequest(
            idea="ESP32 plant watering system",
            platform="esp32",
            available_parts=("ESP32 development board", "Breadboard"),
        )
        plan = create_plan(request)
        names = [c.name.lower() for c in plan.components]
        self.assertNotIn("esp32 development board", names)
        self.assertNotIn("breadboard", names)
        self.assertTrue(any("soil" in name for name in names))

    def test_journal_update_records_milestone(self):
        with tempfile.TemporaryDirectory() as directory:
            journal_path = Path(directory) / "BUILD_JOURNAL.json"
            from vison.forge import update_build_journal
            from vison.forge_service import handle_journal_update

            res = update_build_journal(journal_path, "Dry-sensor test complete", next_action="Pump test")
            self.assertEqual(len(res["completed"]), 1)
            self.assertEqual(res["next_action"], "Pump test")

            text_res = handle_journal_update("completed: pump test passed", journal_path=journal_path)
            self.assertIn("Build Journal Updated", text_res)
            self.assertIn("Total Milestones Completed:** 2", text_res)

    def test_multiturn_ready_delivers_build_pack(self):
        session_id = "test-session-user-123"
        # Turn 1: Project description
        turn1 = run_forge(
            "I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.",
            enable_live_research=False,
            session_id=session_id,
        )
        self.assertIn("Vison Forge Build Assessment", turn1)
        self.assertIn("Ready", turn1)

        # Turn 2: Mention with "i am ready"
        turn2 = run_forge(
            "@agent1qff49pfwt4d480grfvgeqwd4qfcqh4e979x3gjzlqjke2fcrerv3yutu2tz i am ready",
            enable_live_research=False,
            session_id=session_id,
        )
        self.assertIn("Official Project Build Pack", turn2)
        self.assertIn("Bill of Materials", turn2)
        self.assertIn("Ordered Build Steps", turn2)
        self.assertIn("Wiring Blueprint", turn2)
        self.assertIn("Hackathon Submission Checklist", turn2)
