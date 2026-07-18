from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "skills" / "team-mode" / "scripts" / "usage_by_model.py"
SPEC = importlib.util.spec_from_file_location("usage_by_model", SCRIPT)
assert SPEC and SPEC.loader
usage_by_model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(usage_by_model)


def event(kind: str, payload: dict) -> str:
    return json.dumps({"type": kind, "payload": payload}) + "\n"


def write_trace(
    root: Path,
    filename: str,
    *,
    session_id: str,
    task_id: str | None,
    role: str | None,
    agent_path: str | None,
    model: str,
    effort: str,
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
    parent_thread_id: str | None = None,
    legacy: bool = False,
) -> None:
    path = root / "2026" / "07" / "17" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    parent_thread_id = parent_thread_id or (task_id if task_id and session_id != task_id else None)
    payload = {"id": session_id, "cwd": "/workspace"}
    if legacy:
        if parent_thread_id:
            spawn = {"parent_thread_id": parent_thread_id}
            if role:
                spawn["agent_role"] = role
            if agent_path:
                spawn["agent_path"] = agent_path
            payload["source"] = {"subagent": {"thread_spawn": spawn}}
        else:
            payload["source"] = "vscode"
    else:
        payload.update({
            "session_id": task_id,
            "parent_thread_id": parent_thread_id,
            "agent_role": role,
            "agent_path": agent_path,
        })
    usage = {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 7,
    }
    path.write_text(
        event("session_meta", payload)
        + event("turn_context", {"model": model, "effort": effort})
        + event("event_msg", {"type": "token_count", "info": {"last_token_usage": usage}}),
        encoding="utf-8",
    )


class UsageByModelTests(unittest.TestCase):
    def test_task_filter_includes_root_and_children_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_trace(
                root,
                "root.jsonl",
                session_id="task-a",
                task_id="task-a",
                role=None,
                agent_path=None,
                model="gpt-5.6-sol",
                effort="xhigh",
                input_tokens=100,
                cached_tokens=40,
                output_tokens=10,
            )
            write_trace(
                root,
                "child.jsonl",
                session_id="child-a",
                task_id="task-a",
                role="Explorer",
                agent_path="/root/explore",
                model="gpt-5.6-luna",
                effort="medium",
                input_tokens=50,
                cached_tokens=20,
                output_tokens=5,
            )
            write_trace(
                root,
                "other.jsonl",
                session_id="task-b",
                task_id="task-b",
                role=None,
                agent_path=None,
                model="gpt-5.6-sol",
                effort="high",
                input_tokens=999,
                cached_tokens=0,
                output_tokens=999,
            )

            by_model, by_agent, sessions, scanned, included, malformed, resolved = usage_by_model.scan(
                root, None, "task-a"
            )

            self.assertEqual((scanned, included, malformed), (3, 2, 0))
            self.assertEqual(resolved, "task-a")
            self.assertEqual(by_model["gpt-5.6-sol"]["input"], 100)
            self.assertEqual(by_model["gpt-5.6-luna"]["input"], 50)
            self.assertEqual(by_agent["main · gpt-5.6-sol"]["output"], 10)
            self.assertEqual(by_agent["Explorer · gpt-5.6-luna"]["output"], 5)
            details = usage_by_model.session_rows(sessions)
            self.assertEqual({row["session_id"] for row in details}, {"task-a", "child-a"})
            explorer = next(row for row in details if row["agent_role"] == "Explorer")
            self.assertEqual(explorer["effort"], "medium")
            self.assertEqual(explorer["task_id"], "task-a")

    def test_legacy_parent_chain_and_roleless_child_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_trace(
                root, "root.jsonl", session_id="legacy-root", task_id=None, role=None,
                agent_path=None, model="gpt-5.6-sol", effort="high", input_tokens=100,
                cached_tokens=50, output_tokens=10, legacy=True,
            )
            write_trace(
                root, "child.jsonl", session_id="legacy-child", task_id=None, role="Explorer",
                agent_path="/root/explore", model="gpt-5.6-luna", effort="medium",
                input_tokens=50, cached_tokens=25, output_tokens=5,
                parent_thread_id="legacy-root", legacy=True,
            )
            write_trace(
                root, "grandchild.jsonl", session_id="legacy-grandchild", task_id=None, role=None,
                agent_path="/root/explore/helper", model="gpt-5.6-luna", effort="medium",
                input_tokens=25, cached_tokens=10, output_tokens=3,
                parent_thread_id="legacy-child", legacy=True,
            )

            _, by_agent, sessions, _, included, _, resolved = usage_by_model.scan(
                root, None, "legacy-root"
            )

            self.assertEqual((included, resolved), (3, "legacy-root"))
            self.assertEqual(by_agent["main · gpt-5.6-sol"]["input"], 100)
            self.assertEqual(by_agent["Explorer · gpt-5.6-luna"]["input"], 50)
            self.assertEqual(by_agent["subagent/unknown · gpt-5.6-luna"]["input"], 25)
            details = usage_by_model.session_rows(sessions)
            grandchild = next(row for row in details if row["session_id"] == "legacy-grandchild")
            self.assertEqual(grandchild["task_id"], "legacy-root")
            self.assertEqual(grandchild["agent_role"], "subagent/unknown")

    def test_current_child_session_resolves_to_root_task(self) -> None:
        argv = [str(SCRIPT), "--task-id", "current"]
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "child-current"}
        ):
            args = usage_by_model.parse_args()
        self.assertEqual(args.task_id, "child-current")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_trace(
                root, "root.jsonl", session_id="task-current", task_id="task-current", role=None,
                agent_path=None, model="gpt-5.6-sol", effort="xhigh", input_tokens=100,
                cached_tokens=50, output_tokens=10,
            )
            write_trace(
                root, "child.jsonl", session_id="child-current", task_id="task-current",
                role="Reviewer", agent_path="/root/review", model="gpt-5.6-sol",
                effort="high", input_tokens=50, cached_tokens=25, output_tokens=5,
            )
            _, _, _, _, included, _, resolved = usage_by_model.scan(root, None, args.task_id)
            self.assertEqual((included, resolved), (2, "task-current"))

    def test_session_rows_preserve_effort_changes_within_one_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "2026" / "07" / "17" / "mixed.jsonl"
            path.parent.mkdir(parents=True)
            payload = {"id": "task-mixed", "session_id": "task-mixed", "cwd": "/workspace"}
            first = {"input_tokens": 100, "cached_input_tokens": 50, "output_tokens": 10}
            second = {"input_tokens": 200, "cached_input_tokens": 100, "output_tokens": 20}
            path.write_text(
                event("session_meta", payload)
                + event("turn_context", {"model": "gpt-5.6-sol", "effort": "high"})
                + event("event_msg", {"type": "token_count", "info": {"last_token_usage": first}})
                + event("turn_context", {"model": "gpt-5.6-sol", "effort": "xhigh"})
                + event("event_msg", {"type": "token_count", "info": {"last_token_usage": second}}),
                encoding="utf-8",
            )

            by_model, _, sessions, _, _, _, _ = usage_by_model.scan(root, None, "task-mixed")
            self.assertEqual(by_model["gpt-5.6-sol"]["input"], 300)
            details = usage_by_model.session_rows(sessions)
            self.assertEqual({row["effort"] for row in details}, {"high", "xhigh"})
            self.assertEqual(len(details), 2)


if __name__ == "__main__":
    unittest.main()
