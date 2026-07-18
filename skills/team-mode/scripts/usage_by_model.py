#!/usr/bin/env python3
"""Summarize locally retained Codex token usage by model, task, and Agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


RATE_DATE = "2026-07-17"
RATES = {
    "gpt-5.6-luna": {"input": 25.0, "cached": 2.5, "output": 150.0},
    "gpt-5.6-terra": {"input": 62.5, "cached": 6.25, "output": 375.0},
    "gpt-5.6-sol": {"input": 125.0, "cached": 12.5, "output": 750.0},
}


def default_sessions_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home) if codex_home else Path.home() / ".codex") / "sessions"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report locally retained Codex token usage and estimated Standard credits by model."
    )
    period = parser.add_mutually_exclusive_group()
    period.add_argument("--days", type=int, default=1, help="Include the last N local calendar days (default: 1).")
    period.add_argument("--all", action="store_true", help="Include every retained local session.")
    period.add_argument(
        "--task-id",
        metavar="ID|current",
        help="Include one root task and its subagents; 'current' reads CODEX_THREAD_ID.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--by-agent", action="store_true", help="Also group usage by custom Agent role.")
    parser.add_argument("--by-session", action="store_true", help="Also show each root or subagent session separately.")
    parser.add_argument("--sessions-root", type=Path, default=default_sessions_root(), help="Override the sessions directory.")
    args = parser.parse_args()
    if not args.all and args.days < 1:
        parser.error("--days must be at least 1")
    if args.task_id == "current":
        args.task_id = os.environ.get("CODEX_THREAD_ID")
        if not args.task_id:
            parser.error("--task-id current requires CODEX_THREAD_ID")
    return args


def session_date(path: Path, root: Path) -> date:
    try:
        year, month, day = path.relative_to(root).parts[:3]
        return date(int(year), int(month), int(day))
    except (ValueError, IndexError):
        return date.fromtimestamp(path.stat().st_mtime)


def trace_files(root: Path, cutoff: date | None) -> Iterable[Path]:
    for path in root.rglob("*.jsonl"):
        if cutoff is None or session_date(path, root) >= cutoff:
            yield path


def nested_spawn(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source")
    if not isinstance(source, dict):
        return {}
    subagent = source.get("subagent")
    if not isinstance(subagent, dict):
        return {}
    spawn = subagent.get("thread_spawn")
    return spawn if isinstance(spawn, dict) else {}


def read_trace_metadata(path: Path) -> tuple[dict[str, Any], int]:
    malformed = 0
    try:
        lines = path.open("r", encoding="utf-8")
    except OSError:
        return {}, malformed
    with lines:
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if event.get("type") != "session_meta":
                continue
            payload = event.get("payload") or {}
            spawn = nested_spawn(payload)
            session_id = payload.get("id") or path.stem
            parent_thread_id = payload.get("parent_thread_id") or spawn.get("parent_thread_id")
            is_child = bool(parent_thread_id or spawn)
            role = payload.get("agent_role") or spawn.get("agent_role")
            return {
                "path": path,
                "session_id": session_id,
                "task_hint": payload.get("session_id"),
                "parent_thread_id": parent_thread_id,
                "agent_role": role or ("subagent/unknown" if is_child else "main"),
                "agent_path": payload.get("agent_path") or spawn.get("agent_path"),
                "cwd": payload.get("cwd"),
            }, malformed
    return {}, malformed


def resolve_trace_tasks(metadata: list[dict[str, Any]]) -> None:
    by_session = {item["session_id"]: item for item in metadata}

    def resolve(item: dict[str, Any]) -> str:
        task_hint = item.get("task_hint")
        if isinstance(task_hint, str) and task_hint:
            return task_hint
        current = item
        seen: set[str] = set()
        while True:
            session_id = str(current["session_id"])
            if session_id in seen:
                return session_id
            seen.add(session_id)
            parent = current.get("parent_thread_id")
            if not isinstance(parent, str) or not parent:
                return session_id
            parent_metadata = by_session.get(parent)
            if parent_metadata is None:
                return parent
            task_hint = parent_metadata.get("task_hint")
            if isinstance(task_hint, str) and task_hint:
                return task_hint
            current = parent_metadata

    for item in metadata:
        item["task_id"] = resolve(item)


def discover_traces(root: Path, cutoff: date | None) -> tuple[list[dict[str, Any]], int, int]:
    metadata: list[dict[str, Any]] = []
    file_count = 0
    malformed = 0
    for path in trace_files(root, cutoff):
        file_count += 1
        item, item_malformed = read_trace_metadata(path)
        malformed += item_malformed
        if item:
            metadata.append(item)
    resolve_trace_tasks(metadata)
    by_session = {item["session_id"]: item for item in metadata}
    def depth(item: dict[str, Any]) -> int:
        current = item
        seen: set[str] = set()
        value = 0
        while True:
            sid = str(current.get("session_id"))
            if sid in seen:
                return value
            seen.add(sid)
            parent = current.get("parent_thread_id")
            if not parent or parent not in by_session:
                return value
            value += 1
            current = by_session[parent]
    for item in metadata:
        item["depth"] = depth(item)
    return metadata, file_count, malformed


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def resolve_requested_task(metadata: list[dict[str, Any]], requested_id: str | None) -> str | None:
    if requested_id is None:
        return None
    for item in metadata:
        if item["session_id"] == requested_id:
            return str(item["task_id"])
    return requested_id


def blank_usage() -> dict[str, int]:
    return {"events": 0, "input": 0, "cached": 0, "output": 0, "reasoning": 0}


def add_usage(target: dict[str, int], usage: dict[str, Any]) -> None:
    target["events"] += 1
    target["input"] += int(usage.get("input_tokens") or 0)
    target["cached"] += int(usage.get("cached_input_tokens") or 0)
    target["output"] += int(usage.get("output_tokens") or 0)
    target["reasoning"] += int(usage.get("reasoning_output_tokens") or 0)


def merge_usage(target: dict[str, int], source: dict[str, int]) -> None:
    for key in target:
        target[key] += source[key]


def scan(
    root: Path,
    cutoff: date | None,
    task_id: str | None = None,
) -> tuple[
    dict[str, dict[str, int]],
    dict[str, dict[str, int]],
    list[dict[str, Any]],
    int,
    int,
    int,
    str | None,
]:
    by_model: dict[str, dict[str, int]] = defaultdict(blank_usage)
    by_agent: dict[str, dict[str, int]] = defaultdict(blank_usage)
    sessions: list[dict[str, Any]] = []
    metadata, file_count, malformed_lines = discover_traces(root, cutoff)
    resolved_task_id = resolve_requested_task(metadata, task_id)
    included_count = 0

    for trace in metadata:
        if resolved_task_id is not None and trace["task_id"] != resolved_task_id:
            continue
        path = trace["path"]
        included_count += 1
        model: str | None = None
        effort: str | None = None
        usage_by_segment: dict[tuple[str, str | None], dict[str, int]] = defaultdict(blank_usage)
        timestamps: list[datetime] = []
        sandboxes: set[str] = set()
        approvals: set[str] = set()
        interrupted_count = 0
        has_complete = False
        last_terminal: str | None = None
        try:
            lines = path.open("r", encoding="utf-8")
        except OSError:
            continue
        seen_metadata = False
        with lines:
            for line in lines:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    if seen_metadata:
                        malformed_lines += 1
                    continue
                payload = event.get("payload") or {}
                timestamp = parse_timestamp(event.get("timestamp") or payload.get("timestamp"))
                if timestamp:
                    timestamps.append(timestamp)
                if event.get("type") == "session_meta":
                    seen_metadata = True
                elif event.get("type") == "turn_context":
                    model = payload.get("model") or model
                    effort = payload.get("effort")
                    sandbox = payload.get("sandbox_policy")
                    if isinstance(sandbox, dict):
                        sandbox = sandbox.get("type")
                    if isinstance(sandbox, str) and sandbox:
                        sandboxes.add(sandbox)
                    approval = payload.get("approval_policy")
                    if isinstance(approval, str) and approval:
                        approvals.add(approval)
                elif event.get("type") == "event_msg":
                    event_kind = payload.get("type")
                    if event_kind == "task_complete":
                        has_complete = True
                        last_terminal = "completed"
                    elif event_kind == "task_started":
                        last_terminal = None
                    elif event_kind == "turn_aborted":
                        interrupted_count += 1
                        last_terminal = "interrupted"
                if (
                    event.get("type") == "event_msg"
                    and payload.get("type") == "token_count"
                    and model
                ):
                    usage = ((payload.get("info") or {}).get("last_token_usage"))
                    if usage:
                        add_usage(usage_by_segment[(model, effort)], usage)
        role = trace["agent_role"]
        started = min(timestamps) if timestamps else None
        ended = max(timestamps) if timestamps else None
        terminal = last_terminal or "incomplete"
        if not usage_by_segment and model:
            usage_by_segment[(model, effort)]
        for (session_model, session_effort), usage in usage_by_segment.items():
            merge_usage(by_model[session_model], usage)
            merge_usage(by_agent[f"{role} · {session_model}"], usage)
            sessions.append({
                **trace,
                "model": session_model,
                "effort": session_effort,
                "usage": usage,
                "started_at": started.isoformat().replace("+00:00", "Z") if started else None,
                "ended_at": ended.isoformat().replace("+00:00", "Z") if ended else None,
                "elapsed_seconds": (ended - started).total_seconds() if started and ended else None,
                "terminal_status": terminal,
                "final_report_present": has_complete,
                "interrupted_count": interrupted_count,
                "effective_sandbox": sorted(sandboxes),
                "approval_policy": sorted(approvals),
            })
    return (
        dict(by_model),
        dict(by_agent),
        sessions,
        file_count,
        included_count,
        malformed_lines,
        resolved_task_id,
    )


def usage_row(name: str, usage: dict[str, int]) -> dict[str, Any]:
    uncached = max(usage["input"] - usage["cached"], 0)
    rate = RATES.get(name.split(" · ")[-1])
    credits = None
    if rate:
        credits = (
            uncached * rate["input"]
            + usage["cached"] * rate["cached"]
            + usage["output"] * rate["output"]
        ) / 1_000_000
    return {
        "name": name,
        "token_events": usage["events"],
        "input_tokens": usage["input"],
        "cached_input_tokens": usage["cached"],
        "uncached_input_tokens": uncached,
        "output_tokens": usage["output"],
        "reasoning_output_tokens": usage["reasoning"],
        "estimated_standard_credits": credits,
    }


def add_credit_shares(result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known_total = sum(row["estimated_standard_credits"] or 0 for row in result)
    for row in result:
        credits = row["estimated_standard_credits"]
        row["known_credit_share_percent"] = (credits / known_total * 100) if credits is not None and known_total else None
    return result


def rows(source: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    return add_credit_shares([usage_row(name, usage) for name, usage in sorted(source.items())])


def session_rows(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for session in sessions:
        role = session["agent_role"]
        model = session["model"]
        result.append({
            **usage_row(f"{role} · {model}", session["usage"]),
            "session_id": session["session_id"],
            "task_id": session["task_id"],
            "parent_thread_id": session["parent_thread_id"],
            "agent_role": role,
            "agent_path": session["agent_path"],
            "model": model,
            "effort": session["effort"],
            "cwd": session["cwd"],
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at"),
            "elapsed_seconds": session.get("elapsed_seconds"),
            "terminal_status": session.get("terminal_status", "incomplete"),
            "final_report_present": session.get("final_report_present", False),
            "interrupted_count": session.get("interrupted_count", 0),
            "effective_sandbox": session.get("effective_sandbox", []),
            "approval_policy": session.get("approval_policy", []),
            "depth": session.get("depth", 0),
        })
    result.sort(key=lambda row: (row["agent_path"] or "/root", row["session_id"], row["model"]))
    return add_credit_shares(result)


def print_table(title: str, data: list[dict[str, Any]]) -> None:
    print(title)
    print(f"{'Model / Agent':<34} {'Input':>14} {'Cached':>14} {'Output':>12} {'Reason':>12} {'Credits*':>12} {'Share':>8}")
    print("-" * 112)
    for row in data:
        credits = row["estimated_standard_credits"]
        share = row["known_credit_share_percent"]
        credits_text = f"{credits:,.2f}" if credits is not None else "n/a"
        share_text = f"{share:.2f}%" if share is not None else "n/a"
        print(
            f"{row['name']:<34} "
            f"{row['input_tokens']:>14,} "
            f"{row['cached_input_tokens']:>14,} "
            f"{row['output_tokens']:>12,} "
            f"{row['reasoning_output_tokens']:>12,} "
            f"{credits_text:>12} "
            f"{share_text:>8}"
        )
    print()


def print_session_table(data: list[dict[str, Any]]) -> None:
    print("By session")
    print(f"{'Role / Model':<26} {'Agent path':<22} {'Status':<11} {'Elapsed':>8} {'Sandbox':<16} {'Input':>10} {'Output':>9} {'Credits*':>10}")
    print("-" * 114)
    for row in data:
        credits = row["estimated_standard_credits"]
        credits_text = f"{credits:,.2f}" if credits is not None else "n/a"
        elapsed = f"{row['elapsed_seconds']:.1f}s" if row.get("elapsed_seconds") is not None else "n/a"
        sandbox = ",".join(row.get("effective_sandbox") or []) or "n/a"
        print(
            f"{row['name']:<26} {(row['agent_path'] or '/root'):<22} "
            f"{row.get('terminal_status', 'incomplete'):<11} {elapsed:>8} {sandbox:<16} "
            f"{row['input_tokens']:>10,} {row['output_tokens']:>9,} {credits_text:>10}"
        )
    print()


def main() -> int:
    args = parse_args()
    root = args.sessions_root.expanduser().resolve()
    if not root.is_dir():
        print(f"Sessions directory not found: {root}", file=sys.stderr)
        return 2

    cutoff = None if args.all or args.task_id else date.today() - timedelta(days=args.days - 1)
    (
        by_model,
        by_agent,
        sessions,
        file_count,
        included_count,
        malformed,
        resolved_task_id,
    ) = scan(root, cutoff, args.task_id)
    if args.task_id and not included_count:
        print(f"Task not found in retained local sessions: {args.task_id}", file=sys.stderr)
        return 2
    model_rows = rows(by_model)
    agent_rows = rows(by_agent) if args.by_agent else []
    all_session_details = session_rows(sessions)
    detailed_sessions = all_session_details if args.by_session else []
    if resolved_task_id:
        period = f"task {resolved_task_id}"
    else:
        period = "all retained sessions" if cutoff is None else f"{cutoff.isoformat()} through {date.today().isoformat()}"
    limitations = [
        "Local retained sessions only; ephemeral and unavailable remote sessions are excluded.",
        "Credits use configured Standard rates and do not detect mixed Fast usage.",
        "Account limits and resets remain authoritative in Codex /usage.",
        "Runtime fields come from local trace events; completed means only that the session has task_complete, not that artifact quality is assured.",
    ]
    status_counts = {status: sum(1 for row in all_session_details if row.get("terminal_status") == status)
                     for status in ("completed", "interrupted", "incomplete")}
    max_depth = max((row.get("depth", 0) for row in all_session_details), default=0)

    if args.json:
        print(json.dumps({
            "period": period,
            "task_id": resolved_task_id,
            "requested_task_or_session_id": args.task_id,
            "sessions_root": str(root),
            "files_scanned": file_count,
            "session_files_included": included_count,
            "malformed_lines_skipped": malformed,
            "credit_rates_as_of": RATE_DATE,
            "models": model_rows,
            "agents": agent_rows,
            "sessions": detailed_sessions,
            "session_status_counts": status_counts,
            "max_subagent_depth": max_depth,
            "limitations": limitations,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"Codex local usage · {period}")
    print(f"Scanned {file_count} session files · included {included_count} · Standard credit rates as of {RATE_DATE}")
    print()
    print_table("By model", model_rows)
    if args.by_agent:
        print_table("By Agent role", agent_rows)
    if args.by_session:
        print_session_table(detailed_sessions)
    print("* Estimated Standard credits. " + " ".join(limitations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
