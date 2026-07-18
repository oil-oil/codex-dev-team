from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROFILES = {
    "default.toml": ("default", "gpt-5.6-terra", "low", "read-only"),
    "Explorer.toml": ("Explorer", "gpt-5.6-luna", "medium", "read-only"),
    "Executor.toml": ("Executor", "gpt-5.6-luna", "medium", "workspace-write"),
    "Complex Executor.toml": ("Complex Executor", "gpt-5.6-sol", "high", "workspace-write"),
    "Reviewer.toml": ("Reviewer", "gpt-5.6-sol", "high", "read-only"),
}


class AgentProfileTests(unittest.TestCase):
    def test_profile_boundaries_and_models_are_explicit(self) -> None:
        for filename, expected in PROFILES.items():
            with self.subTest(filename=filename):
                data = tomllib.loads((ROOT / "agents" / filename).read_text(encoding="utf-8"))
                actual = (
                    data["name"],
                    data["model"],
                    data["model_reasoning_effort"],
                    data["sandbox_mode"],
                )
                self.assertEqual(actual, expected)
                if filename != "default.toml":
                    self.assertIn(
                        "Do not spawn subagents; return evidence or blockers to the parent.",
                        data["developer_instructions"],
                    )

    def test_default_profile_fails_closed(self) -> None:
        data = tomllib.loads((ROOT / "agents" / "default.toml").read_text(encoding="utf-8"))
        instructions = data["developer_instructions"]
        self.assertIn("dispatch guard, not a working subagent", instructions)
        self.assertIn("Do not inspect files, call tools, spawn", instructions)
        self.assertIn("DISPATCH BLOCKED", instructions)
        self.assertIn("the delegated task was not executed", instructions)
        self.assertIn("agent_type was omitted or set to default", instructions)

    def test_complex_executor_reports_risk_without_recommending_another_agent(self) -> None:
        data = tomllib.loads((ROOT / "agents" / "Complex Executor.toml").read_text(encoding="utf-8"))
        instructions = data["developer_instructions"]
        self.assertIn("Do not recommend or name another Agent as the next step.", instructions)
        self.assertIn("without recommending another Agent", instructions)
        self.assertNotIn("warrant a fresh `Reviewer`", instructions)
        self.assertNotIn("requires an independent handoff", instructions)

    def test_reviewer_is_bounded_by_the_review_packet(self) -> None:
        data = tomllib.loads((ROOT / "agents" / "Reviewer.toml").read_text(encoding="utf-8"))
        instructions = data["developer_instructions"]
        self.assertIn("passed checks, exclusions, and stop condition", instructions)
        self.assertIn("Do not repeat broad validation that already passed", instructions)
        self.assertIn("return a usable partial verdict immediately", instructions)


if __name__ == "__main__":
    unittest.main()
