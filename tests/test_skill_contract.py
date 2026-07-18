from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class TeamModeSkillContractTests(unittest.TestCase):
    def test_dispatch_contract_is_operational(self) -> None:
        skill = (ROOT / "skills" / "team-mode" / "SKILL.md").read_text(encoding="utf-8")
        for label in ("Outcome", "Benefit", "Sources", "Scope", "Checks", "Stop when", "Return"):
            with self.subTest(label=label):
                self.assertIn(f"`{label}`", skill)
        for label in ("Unresolved risk", "Evidence", "Checks already passed", "Do not repeat"):
            with self.subTest(label=label):
                self.assertIn(f"`{label}`", skill)
        self.assertIn("usable partial verdict", skill)
        self.assertIn("children never spawn descendants", skill)
        self.assertIn("request a partial verdict once, then interrupt it", skill)

    def test_agent_type_dispatch_gate_is_explicit(self) -> None:
        skill = (ROOT / "skills" / "team-mode" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Dispatch Gate", skill)
        self.assertIn("Every `spawn_agent` call must explicitly pass `agent_type`", skill)
        self.assertIn("Never omit `agent_type` and never pass `default`", skill)
        self.assertIn("`default` profile is a fail-closed dispatch guard", skill)
        self.assertIn("only time Team Mode deliberately omits `agent_type`", skill)
        self.assertIn("## One-Time Onboarding", skill)
        self.assertIn("Do not inspect Agent files", skill)
        self.assertIn("skip onboarding without mentioning it", skill)

    def test_custom_agent_reference_matches_current_runtime_contract(self) -> None:
        reference = (ROOT / "skills" / "team-mode" / "references" / "custom-agents.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Current Codex releases enable subagent workflows by default", reference)
        self.assertIn("max_depth = 1", reference)
        self.assertIn("actual runtime trace", reference)
        self.assertIn("four working profiles plus one fail-closed `default` guard", reference)
        self.assertIn("gpt-5.6-terra", reference)
        self.assertIn("## Run Onboarding Once", reference)
        self.assertIn("DISPATCH BLOCKED", reference)
        self.assertIn("## Explain How To Disable The Guard", reference)
        self.assertIn("~/.codex/agents-disabled/default.toml", reference)
        self.assertNotIn("features enable multi_agent_v2", reference)


if __name__ == "__main__":
    unittest.main()
