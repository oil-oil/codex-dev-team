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


def event(kind: str, payload: dict, timestamp: str | None = None) -> str:
    value = {"type": kind, "payload": payload}
    if timestamp:
        value["timestamp"] = timestamp
    return json.dumps(value) + "\n"


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
    started_at: str | None = None,
    ended_at: str | None = None,
    terminal: str | None = None,
    sandbox: str | None = None,
    approval: str | None = None,
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
    context = {"model": model, "effort": effort}
    if sandbox:
        context["sandbox_policy"] = {"type": sandbox}
    if approval:
        context["approval_policy"] = approval
    content = event("session_meta", payload)
    content += event("turn_context", context, started_at)
    content += event("event_msg", {"type": "token_count", "info": {"last_token_usage": usage}}, started_at)
    if terminal == "completed":
        content += event("event_msg", {"type": "task_complete"}, ended_at)
    elif terminal == "interrupted":
        content += event("event_msg", {"type": "turn_aborted"}, ended_at)
    path.write_text(content, encoding="utf-8")


class UsageByModelTests(unittest.TestCase):
    def test_usage_row_exposes_token_totals_credit_components_and_effective_ratio(self) -> None:
        row = usage_by_model.usage_row(
            "gpt-5.6-sol",
            {"events": 1, "input": 100, "cached": 40, "output": 10, "reasoning": 7},
        )

        self.assertEqual(row["total_processed_tokens"], 110)
        self.assertEqual(row["uncached_input_tokens"], 60)
        self.assertEqual(row["reasoning_output_tokens"], 7)
        self.assertAlmostEqual(row["estimated_standard_credits"], 0.0155)
        self.assertEqual(
            row["estimated_standard_credit_breakdown"],
            {"uncached_input": 0.0075, "cached_input": 0.0005, "output": 0.0075},
        )
        self.assertAlmostEqual(row["effective_processed_tokens_per_credit"], 110 / 0.0155)

    def test_rate_card_exposes_type_specific_token_equivalents(self) -> None:
        cards = {row["model"]: row for row in usage_by_model.rate_card_rows()}

        self.assertEqual(cards["gpt-5.6-sol"]["tokens_per_credit"]["uncached_input"], 8_000)
        self.assertEqual(cards["gpt-5.6-sol"]["tokens_per_credit"]["cached_input"], 80_000)
        self.assertAlmostEqual(cards["gpt-5.6-sol"]["tokens_per_credit"]["output"], 4_000 / 3)
        self.assertEqual(cards["gpt-5.6-luna"]["tokens_per_credit"]["uncached_input"], 40_000)
        self.assertEqual(cards["gpt-5.6-luna"]["tokens_per_credit"]["cached_input"], 400_000)
        self.assertAlmostEqual(cards["gpt-5.6-luna"]["tokens_per_credit"]["output"], 20_000 / 3)

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

    def test_runtime_status_timestamps_sandbox_and_depth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_trace(root, "root.jsonl", session_id="root", task_id="root", role=None,
                        agent_path=None, model="gpt-5.6-sol", effort="high", input_tokens=1,
                        cached_tokens=0, output_tokens=1, started_at="2026-07-17T00:00:00Z",
                        ended_at="2026-07-17T00:00:05Z", terminal="completed",
                        sandbox="workspace-write", approval="on-request")
            write_trace(root, "child.jsonl", session_id="child", task_id="root", role="Explorer",
                        agent_path="/root/child", model="gpt-5.6-luna", effort="medium", input_tokens=1,
                        cached_tokens=0, output_tokens=1, parent_thread_id="root",
                        started_at="2026-07-17T00:01:00Z", ended_at="2026-07-17T00:01:02Z",
                        terminal="interrupted", sandbox="read-only", approval="never")
            write_trace(root, "grandchild.jsonl", session_id="grandchild", task_id="root", role="Explorer",
                        agent_path="/root/child/g", model="gpt-5.6-luna", effort="medium", input_tokens=1,
                        cached_tokens=0, output_tokens=1, parent_thread_id="child")
            _, _, sessions, *_ = usage_by_model.scan(root, None, "root")
            details = usage_by_model.session_rows(sessions)
            root_row = next(r for r in details if r["session_id"] == "root")
            child_row = next(r for r in details if r["session_id"] == "child")
            grand_row = next(r for r in details if r["session_id"] == "grandchild")
            self.assertEqual(root_row["terminal_status"], "completed")
            self.assertTrue(root_row["final_report_present"])
            self.assertEqual(root_row["elapsed_seconds"], 5.0)
            self.assertEqual(root_row["effective_sandbox"], ["workspace-write"])
            self.assertEqual(child_row["terminal_status"], "interrupted")
            self.assertEqual(child_row["interrupted_count"], 1)
            self.assertEqual(child_row["depth"], 1)
            self.assertEqual(grand_row["terminal_status"], "incomplete")
            self.assertEqual(grand_row["depth"], 2)

    def test_latest_terminal_marker_wins_but_prior_final_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "2026" / "07" / "17" / "followup.jsonl"
            path.parent.mkdir(parents=True)
            payload = {"id": "followup", "session_id": "followup", "cwd": "/workspace"}
            usage = {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}
            path.write_text(
                event("session_meta", payload, "2026-07-17T00:00:00Z")
                + event("turn_context", {"model": "gpt-5.6-sol", "effort": "high"})
                + event("event_msg", {"type": "token_count", "info": {"last_token_usage": usage}})
                + event("event_msg", {"type": "task_complete"}, "2026-07-17T00:00:01Z")
                + event("event_msg", {"type": "turn_aborted"}, "2026-07-17T00:00:02Z"),
                encoding="utf-8",
            )
            _, _, sessions, *_ = usage_by_model.scan(root, None, "followup")
            row = usage_by_model.session_rows(sessions)[0]
            self.assertEqual(row["terminal_status"], "interrupted")
            self.assertTrue(row["final_report_present"])
            self.assertEqual(row["interrupted_count"], 1)

    def test_resumed_session_is_incomplete_until_the_new_turn_finishes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "2026" / "07" / "17" / "resumed.jsonl"
            path.parent.mkdir(parents=True)
            payload = {"id": "resumed", "session_id": "resumed", "cwd": "/workspace"}
            usage = {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}
            path.write_text(
                event("session_meta", payload, "2026-07-17T00:00:00Z")
                + event("turn_context", {"model": "gpt-5.6-sol", "effort": "high"})
                + event("event_msg", {"type": "token_count", "info": {"last_token_usage": usage}})
                + event("event_msg", {"type": "task_complete"}, "2026-07-17T00:00:01Z")
                + event("event_msg", {"type": "task_started"}, "2026-07-17T00:00:02Z"),
                encoding="utf-8",
            )
            _, _, sessions, *_ = usage_by_model.scan(root, None, "resumed")
            row = usage_by_model.session_rows(sessions)[0]
            self.assertEqual(row["terminal_status"], "incomplete")
            self.assertTrue(row["final_report_present"])


if __name__ == "__main__":
    unittest.main()
