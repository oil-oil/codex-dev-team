---
name: team-mode
description: Coordinate custom subagents for substantial development, research, analysis, planning, document, data, and content tasks when delegation, parallel work, context isolation, lower-cost execution, or independent review provides clear value. Keep unresolved decisions and final acceptance in the main thread. Do not use for casual conversation, simple lookups, or tasks whose coordination cost exceeds the work.
---

# Team Mode

Lead the task in the main thread. Use the smallest useful set of subagents to isolate noisy work, reduce expensive main-agent context, run independent work in parallel, or obtain a fresh review. Do not turn the roles into a mandatory pipeline.

## Required Rules

- When this Skill activates, immediately send one brief commentary update in the user's language, prefixed with `👾`. For Chinese, say `👾 已开启小队模式。`; translate naturally for other languages. Announce it once per task, not before every subagent call.
- Activating Team Mode does not require spawning any subagent. Keep clear, short, low-risk work in the main thread when delegation or independent review would cost more than it adds. Do not launch an Executor or Reviewer merely to complete a role sequence.
- Spawn custom profiles through the exact `agent_type`: `Explorer`, `Executor`, `Complex Executor`, or `Reviewer`. `task_name` only labels the child thread. If `agent_type` is unavailable, do not claim that a custom profile was used.
- Use `fork_turns="none"` by default and always for a new `Reviewer`.
- Keep unresolved user intent, product, editorial, architecture, and safety decisions, plus final acceptance, in the main thread.
- Keep one writer per shared artifact, working tree, or mutable system. Parallel writers require isolated targets or disjoint, stable ownership.
- Inspect the actual artifacts, sources, diffs, and verification output before accepting delegated work.
- Treat the parent task's live permission mode as the effective child permission. Do not infer read-only isolation from TOML alone; use the onboarding or diagnostic verification in the reference when permissions need confirmation.

This Skill does not install custom Agent profiles. If an expected profile is unavailable, or the user asks to create, repair, verify, or customize the profiles, read [references/custom-agents.md](references/custom-agents.md). Do not load that reference during normal routing.

## Route The Work

- Use `Explorer` for non-trivial, read-only discovery across current web sources, documents, datasets, codebases, schemas, APIs, logs, or configuration. Give independent slices to separate Explorers. Let the main thread wait when the result blocks the next decision; do not repeat the same exploration.
- Use `Executor` for clear, bounded, low-risk work with deterministic checks when lower-cost execution, context isolation, repetition, or useful parallelism justifies the handoff. Otherwise let the main thread do it directly.
- Use `Complex Executor` for substantial but bounded execution after the main thread has stated the intended outcome, allowed scope, constraints, and required checks.
- Use `Reviewer` only when fresh independent judgment has clear value because the result is complex, consequential, uncertain, difficult to verify, or explicitly requested. Let the main thread verify straightforward low-risk work directly.

After discovery, let the main thread choose whether to continue directly or delegate. Delegate only when bounded execution, context isolation, lower cost, useful parallelism, or independent judgment creates clear value.

## Coordinate The Work

- Start with the minimum useful number of agents. Parallelize only genuinely independent exploration, analysis, tests, triage, production, or review; do not create duplicate work merely to keep agents occupied.
- Before execution, state plainly what the result should be, what may be touched, what must remain unchanged, and how completion will be checked. Revise these requirements if new evidence conflicts with them.
- Verify in proportion to risk. Use independent review for complex, consequential, or difficult-to-check results rather than for every task.

## Context And Reuse

- Give each new subagent a compact, self-contained brief containing only the objective, relevant sources or paths, scope, authority, exclusions, intended result, required checks, and return format. Never copy credentials into it.
- Reuse an existing Explorer or executor when new work belongs to the same task, topic, business area, subsystem, artifact, or workstream and its prior context remains useful. Send only the new objective and changed constraints.
- Start fresh when prior context is stale or noisy, the role or authority changes, or independent judgment matters.
- Reuse a Reviewer only to clarify its existing report. Use a fresh Reviewer for a new review or for checking revised work.
- Do not give an Explorer an expected conclusion. Do not tell a Reviewer the prior debate, author, suspected findings, or desired verdict.

## Handle Findings

- Validate findings against the underlying sources, artifact, and intended outcome before acting.
- Let the main thread apply accepted repairs directly or delegate them according to scope, context, cost, and risk.
- After consequential repairs, use a fresh Reviewer with only the updated artifact and neutral requirements.

## Inspect Local Usage

When the user asks for model or subagent consumption, run `python3 scripts/usage_by_model.py`. Use `--days N`, `--all`, `--json`, or `--by-agent` as requested. This is an on-demand diagnostic, not part of normal routing. Report that local logs exclude ephemeral or unavailable remote sessions, configured credits assume Standard speed, and Codex `/usage` remains authoritative for account limits.

## Guardrails

- Preserve unrelated user work and obey applicable project, domain, and tool instructions.
- Delegation does not expand authority. Do not commit, publish, deploy, send messages, change external state, or handle sensitive data beyond the user's request.
- For current or factual research, prefer primary sources, record relevant dates, cite evidence, and distinguish fact from inference.
- Keep private-data exploration narrow and return only the minimum evidence needed.
- Resolve conflicting claims against the strongest available evidence and return one coherent result to the user.
