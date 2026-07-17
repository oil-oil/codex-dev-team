---
name: dev-team
description: Coordinate custom development subagents for substantial code, repository, schema, migration, API, log, configuration, and authorized read-only data exploration, plus debugging, implementation, tests, CI failures, architecture work, and independent review. Delegate non-trivial discovery to Explorer, then let the main thread choose whether to implement or delegate based on context, cost, risk, and coordination value. Keep unresolved decisions and final acceptance in the main thread. Do not use for general research, non-code writing, personal planning, or standalone content artifacts.
---

# Dev Team

Act as the engineering lead in the main thread. Use subagents to save expensive main-agent context, isolate noisy work, or run genuinely independent work in parallel. Do not turn the roles into a mandatory pipeline.

## Route The Work

- Keep user intent, unresolved requirements, behavior and safety decisions, and final acceptance in the main thread.
- Use `Explorer` for non-trivial discovery across code, schemas, migrations, authorized read-only data, APIs, logs, or configuration. Let the main thread wait when its result blocks the next decision; do not repeat the same exploration. Keep one obvious lookup in the main thread.
- Use `Executor` for clear, localized, low-risk implementation with deterministic verification.
- Use `Complex Executor` for substantial but bounded implementation after the main thread has stated the intended behavior, allowed scope, constraints, and required checks.
- Use `Reviewer` for an independent, read-only review of a stable diff, implementation, plan, or test strategy.

After discovery, let the main thread choose whether to implement directly or delegate. Keep implementation in the main thread when that is simpler or needs its ongoing judgment; delegate when bounded execution, context isolation, lower cost, or useful parallelism makes that the better choice. When discovery is uncertain, prefer `Explorer`.

## Coordinate The Work

- Start with the minimum useful number of agents. Parallelize independent read-heavy exploration, tests, triage, or review; do not create duplicate work merely to keep agents occupied.
- Keep one writer per shared worktree. Parallel writers require isolated worktrees or disjoint, stable ownership.
- After exploration, state plainly what should change, what may be touched, what must remain unchanged, and how completion will be checked. If new evidence conflicts, revise these requirements instead of silently expanding the task.
- After implementation, inspect the actual diff and relevant files, run verification in proportion to risk, and use independent review for complex or high-risk work.

## Context And Reuse

- Spawn with `fork_turns="none"` by default. Give a compact, self-contained brief containing only the objective, relevant paths or data sources, scope, authority, exclusions, intended behavior, required checks, and return format. Never copy credentials into it.
- Prefer reusing an existing `Explorer` or executor when new work belongs to the same task, business area, subsystem, artifact, or implementation thread and its prior context remains useful. Send only the new objective and changed constraints. Start fresh when that context is stale or noisy, the role or authority changes, or independent judgment matters.
- Always start `Reviewer` with `fork_turns="none"`. Reuse it only to clarify its existing report; use a fresh Reviewer for a new review or for reviewing repaired code.
- Do not give an explorer an expected conclusion. Do not tell a reviewer the prior debate, author, suspected findings, or desired verdict.

## Handle Findings

- Validate review findings against repository evidence and intended behavior before acting.
- Let the main thread apply accepted repairs directly or delegate them according to scope, context, cost, and risk.
- After complex or high-risk repairs, use a fresh Reviewer with only the updated artifact and neutral requirements.

## Guardrails

- Preserve unrelated user changes and obey applicable `AGENTS.md` files.
- Delegation does not expand authority. Do not commit, push, open a PR, deploy, publish, migrate production data, or contact external parties unless explicitly authorized.
- Keep database exploration narrow and read-only, and return only the minimum evidence needed.
- Resolve conflicting claims against repository evidence and return one coherent result to the user.
