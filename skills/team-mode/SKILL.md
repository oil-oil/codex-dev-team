---
name: team-mode
description: Coordinate custom subagents for substantial development, research, analysis, planning, document, data, and content tasks when delegation, parallel work, context isolation, lower-cost execution, or independent review provides clear value. Keep unresolved decisions and final acceptance in the main thread. Do not use for casual conversation, simple lookups, or tasks whose coordination cost exceeds the work.
---

# Team Mode

Lead the task in the main thread. Use the smallest useful set of subagents to isolate noisy work, reduce expensive main-agent context, run independent work in parallel, or obtain a fresh review. Do not turn the roles into a mandatory pipeline.

## Dispatch Gate

Every `spawn_agent` call must explicitly pass `agent_type` as exactly one of `Explorer`, `Executor`, `Complex Executor`, or `Reviewer`.

- Never omit `agent_type` and never pass `default`. The `default` profile is a fail-closed dispatch guard, not a working Agent.
- Never use `task_name` to select a profile; it only labels the child thread.
- If the intended custom profile is unavailable, keep the work in the main thread or repair the profiles. Do not silently use a generic child.
- If a child returns the dispatch-guard message or its trace shows `default` / `subagent/unknown`, reject its output and respawn only after selecting the intended custom profile explicitly.

Read [references/custom-agents.md](references/custom-agents.md) only when installing, repairing, or verifying the four working profiles and the `default` guard. The controlled onboarding self-test described there is the only time Team Mode deliberately omits `agent_type`.

## One-Time Onboarding

Do not inspect Agent files, load onboarding instructions, or repeat setup explanations during normal Team Mode routing. Treat the active `spawn_agent.agent_type` choices and descriptions as runtime readiness evidence. When all four working profiles are available and `default` is described as the dispatch guard, skip onboarding without mentioning it.

Only read [references/custom-agents.md](references/custom-agents.md) and start onboarding when a required profile or guard is unavailable, or when the user explicitly asks to install, repair, verify, move, disable, or customize them. Get authorization before writing personal or project configuration. After a successful setup or repair, tell the user once what was installed, which models are assigned, that the guard affects omitted/default subagent dispatches in its installation scope, when restart or a new task is required, and how to disable or restore only the guard without removing the four working profiles.

## Required Rules

- When this Skill activates, immediately send one brief commentary update in the user's language, prefixed with `👾`. For Chinese, say `👾 已开启小队模式。`; translate naturally for other languages. Announce it once per task, not before every subagent call.
- Activating Team Mode does not require spawning any subagent. Keep clear, short, low-risk work in the main thread when delegation or independent review would cost more than it adds. Do not launch an Executor or Reviewer merely to complete a role sequence.
- Before each spawn, identify one material benefit: useful parallelism, context isolation, lower-cost bounded execution, or independent judgment. Count briefing, inspection, rework, and waiting as coordination cost. An explicit Team Mode request activates this routing guide; it does not by itself make a spawn worthwhile.
- Keep all routing and fan-out in the main thread. Under standard Team Mode, children never spawn descendants; they return evidence, artifacts, or blockers to the parent. Treat an explicit user request for recursive delegation as a separate scope expansion with its own permission, depth, and usage decision.
- Use `fork_turns="none"` by default and always for a new `Reviewer`.
- Keep unresolved user intent, product, editorial, architecture, and safety decisions, plus final acceptance, in the main thread.
- Keep one writer per shared artifact, working tree, or mutable system. Parallel writers require isolated targets or disjoint, stable ownership.
- Inspect the actual artifacts, sources, diffs, and verification output before accepting delegated work.
- If a child errors, times out, or is interrupted, inspect shared artifacts and trace evidence before retrying. Retry a transient failure at most once and only when no usable result exists; otherwise recover in the main thread or re-scope the remaining work.
- Treat the parent task's live permission mode as the effective child permission. Do not infer read-only isolation from TOML alone; use the onboarding or diagnostic verification in the reference when permissions need confirmation.

When the user asks to evaluate Team Mode itself, compare models or reasoning effort, or measure whether delegation was worthwhile, read [references/evaluation.md](references/evaluation.md) before designing the trial.

## Dispatch Contract

Before every spawn, make the brief self-contained with these labeled fields:

- `Outcome`: the independently finishable result the child must return.
- `Benefit`: the material advantage over keeping this slice in the main thread.
- `Sources`: every path, URL, dataset, or raw artifact required for factual work.
- `Scope`: allowed reads or writes, ownership, exclusions, and external-action authority.
- `Checks`: acceptance criteria and validation the child owns.
- `Stop when`: the bounded completion, blocker, or evidence threshold that ends the turn.
- `Return`: the concise report or artifact format expected by the parent.

Do not spawn while `Outcome`, `Benefit`, required `Sources`, `Checks`, or `Stop when` is missing. Keep the slice in the main thread when it is not independently finishable or the expected gain does not exceed briefing, waiting, inspection, and possible rework.

For a `Reviewer`, also name one concrete `Unresolved risk`, the exact `Evidence` to inspect, `Checks already passed`, and `Do not repeat`. Ask for findings from that packet first and require a usable partial verdict if the stop condition arrives before exhaustive review.

## Route The Work

- Use `Explorer` for non-trivial, read-only discovery across current web sources, documents, datasets, codebases, schemas, APIs, logs, or configuration. Give independent slices to separate Explorers. Let the main thread wait when the result blocks the next decision; do not repeat the same exploration.
- Use `Executor` for clear, bounded, low-risk work with deterministic checks when lower-cost execution, context isolation, repetition, or useful parallelism justifies the handoff. Otherwise let the main thread do it directly.
- Use `Complex Executor` for substantial but bounded execution after the main thread has stated the intended outcome, allowed scope, constraints, and required checks.
- Use `Reviewer` only when fresh independent judgment has clear value because the result is complex, consequential, uncertain, difficult to verify, or explicitly requested. Let the main thread verify straightforward low-risk work directly. A child's suggestion to add review is evidence, not a routing decision; use the Reviewer packet above instead of treating review as an automatic final stage.

After discovery, let the main thread choose whether to continue directly or delegate. Delegate only when bounded execution, context isolation, lower cost, useful parallelism, or independent judgment creates clear value.

## Coordinate The Work

- Start with the minimum useful number of agents. Parallelize only genuinely independent exploration, analysis, tests, triage, production, or review; do not create duplicate work merely to keep agents occupied.
- Before execution, state plainly what the result should be, what may be touched, what must remain unchanged, and how completion will be checked. Revise these requirements if new evidence conflicts with them.
- Verify in proportion to risk. Use independent review for complex, consequential, or difficult-to-check results rather than for every task.
- Reuse passed checks as evidence. Do not ask another Agent to repeat broad validation unless the integrity or relevance of those checks is itself the unresolved risk.

## Context And Reuse

- Give each new subagent a compact, self-contained brief containing only the objective, relevant sources or paths, scope, authority, exclusions, intended result, required checks, and return format. Never copy credentials into it.
- With `fork_turns="none"`, assume the child knows nothing from the parent conversation. Name every source artifact required for factual claims; if a source is missing, either provide its path, narrow the child to collecting that evidence, or keep the source-dependent slice in the main thread.
- Reuse an existing Explorer or executor when new work belongs to the same task, topic, business area, subsystem, artifact, or workstream and its prior context remains useful. Send only the new objective and changed constraints.
- Start fresh when prior context is stale or noisy, the role or authority changes, or independent judgment matters.
- Reuse a Reviewer only to clarify its existing report. Use a fresh Reviewer for a new review or for checking revised work.
- Do not give an Explorer an expected conclusion. Do not tell a Reviewer the prior debate, author, suspected findings, or desired verdict.

## Handle Findings

- Validate findings against the underlying sources, artifact, and intended outcome before acting.
- Let the main thread apply accepted repairs directly or delegate them according to scope, context, cost, and risk.
- When the risk assessment calls for independent review after consequential repairs, use a fresh Reviewer with only the updated artifact and neutral requirements.
- If a Reviewer crosses its `Stop when` condition without a usable return, request a partial verdict once, then interrupt it. Inspect the trace and existing evidence; do not automatically start another Reviewer.

## Inspect Local Usage

When the user asks for model or subagent consumption, run `python3 scripts/usage_by_model.py`. For the active task use `--task-id current --by-agent --by-session`; for broader history use `--days N` or `--all`, with `--json` when structured output helps. This is an on-demand diagnostic, not part of normal routing. Report that local logs exclude ephemeral or unavailable remote sessions, configured credits assume Standard speed, and Codex `/usage` remains authoritative for account limits.

## Guardrails

- Preserve unrelated user work and obey applicable project, domain, and tool instructions.
- Delegation does not expand authority. Do not commit, publish, deploy, send messages, change external state, or handle sensitive data beyond the user's request.
- For current or factual research, prefer primary sources, record relevant dates, cite evidence, and distinguish fact from inference.
- Keep private-data exploration narrow and return only the minimum evidence needed.
- Resolve conflicting claims against the strongest available evidence and return one coherent result to the user.
