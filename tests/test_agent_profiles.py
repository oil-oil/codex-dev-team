from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROFILES = {
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
                self.assertIn(
                    "Do not spawn subagents unless the parent explicitly delegated a bounded orchestration task.",
                    data["developer_instructions"],
                )

    def test_complex_executor_returns_review_routing_to_parent(self) -> None:
        data = tomllib.loads((ROOT / "agents" / "Complex Executor.toml").read_text(encoding="utf-8"))
        instructions = data["developer_instructions"]
        self.assertIn("the parent can decide whether an independent `Reviewer` adds material value", instructions)
        self.assertNotIn("requires an independent handoff", instructions)


if __name__ == "__main__":
    unittest.main()
