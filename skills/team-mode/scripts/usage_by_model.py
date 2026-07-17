#!/usr/bin/env python3
"""Summarize locally retained Codex token usage by model."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
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
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--by-agent", action="store_true", help="Also group usage by custom Agent role.")
    parser.add_argument("--sessions-root", type=Path, default=default_sessions_root(), help="Override the sessions directory.")
    args = parser.parse_args()
    if not args.all and args.days < 1:
        parser.error("--days must be at least 1")
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


def blank_usage() -> dict[str, int]:
    return {"events": 0, "input": 0, "cached": 0, "output": 0, "reasoning": 0}


def add_usage(target: dict[str, int], usage: dict[str, Any]) -> None:
    target["events"] += 1
    target["input"] += int(usage.get("input_tokens") or 0)
    target["cached"] += int(usage.get("cached_input_tokens") or 0)
    target["output"] += int(usage.get("output_tokens") or 0)
    target["reasoning"] += int(usage.get("reasoning_output_tokens") or 0)


def scan(root: Path, cutoff: date | None) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], int, int]:
    by_model: dict[str, dict[str, int]] = defaultdict(blank_usage)
    by_agent: dict[str, dict[str, int]] = defaultdict(blank_usage)
    file_count = 0
    malformed_lines = 0

    for path in trace_files(root, cutoff):
        file_count += 1
        model: str | None = None
        role = "main"
        try:
            lines = path.open("r", encoding="utf-8")
        except OSError:
            continue
        with lines:
            for line in lines:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    malformed_lines += 1
                    continue
                payload = event.get("payload") or {}
                if event.get("type") == "session_meta":
                    role = payload.get("agent_role") or "main"
                elif event.get("type") == "turn_context":
                    model = payload.get("model") or model
                elif (
                    event.get("type") == "event_msg"
                    and payload.get("type") == "token_count"
                    and model
                ):
                    usage = ((payload.get("info") or {}).get("last_token_usage"))
                    if usage:
                        add_usage(by_model[model], usage)
                        add_usage(by_agent[f"{role} · {model}"], usage)
    return dict(by_model), dict(by_agent), file_count, malformed_lines


def rows(source: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name, usage in sorted(source.items()):
        uncached = max(usage["input"] - usage["cached"], 0)
        rate = RATES.get(name.split(" · ")[-1])
        credits = None
        if rate:
            credits = (
                uncached * rate["input"]
                + usage["cached"] * rate["cached"]
                + usage["output"] * rate["output"]
            ) / 1_000_000
        result.append(
            {
                "name": name,
                "token_events": usage["events"],
                "input_tokens": usage["input"],
                "cached_input_tokens": usage["cached"],
                "uncached_input_tokens": uncached,
                "output_tokens": usage["output"],
                "reasoning_output_tokens": usage["reasoning"],
                "estimated_standard_credits": credits,
            }
        )
    known_total = sum(row["estimated_standard_credits"] or 0 for row in result)
    for row in result:
        credits = row["estimated_standard_credits"]
        row["known_credit_share_percent"] = (credits / known_total * 100) if credits is not None and known_total else None
    return result


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


def main() -> int:
    args = parse_args()
    root = args.sessions_root.expanduser().resolve()
    if not root.is_dir():
        print(f"Sessions directory not found: {root}", file=sys.stderr)
        return 2

    cutoff = None if args.all else date.today() - timedelta(days=args.days - 1)
    by_model, by_agent, file_count, malformed = scan(root, cutoff)
    model_rows = rows(by_model)
    agent_rows = rows(by_agent) if args.by_agent else []
    period = "all retained sessions" if cutoff is None else f"{cutoff.isoformat()} through {date.today().isoformat()}"
    limitations = [
        "Local retained sessions only; ephemeral and unavailable remote sessions are excluded.",
        "Credits use configured Standard rates and do not detect mixed Fast usage.",
        "Account limits and resets remain authoritative in Codex /usage.",
    ]

    if args.json:
        print(json.dumps({
            "period": period,
            "sessions_root": str(root),
            "files_scanned": file_count,
            "malformed_lines_skipped": malformed,
            "credit_rates_as_of": RATE_DATE,
            "models": model_rows,
            "agents": agent_rows,
            "limitations": limitations,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"Codex local usage · {period}")
    print(f"Scanned {file_count} session files · Standard credit rates as of {RATE_DATE}")
    print()
    print_table("By model", model_rows)
    if args.by_agent:
        print_table("By Agent role", agent_rows)
    print("* Estimated Standard credits. " + " ".join(limitations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
