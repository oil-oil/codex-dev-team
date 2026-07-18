# Evaluate Team Mode

Read this reference only when the user asks to assess Team Mode's routing, Agent profiles, models, reasoning effort, cost, or practical value.

## Establish The Trial

1. Record the root task ID, repository or artifact baseline, acceptance checks, and installed role-to-model mapping.
2. Verify actual child runtime metadata from local traces: `agent_role`, `model`, `effort`, and effective sandbox. Configuration files alone do not prove runtime selection or isolation.
3. Choose the smallest useful delegation. Keep a comparable slice in the main thread when the goal includes comparing delegation with direct work.
4. Give different Agents independent slices or one stable writer boundary. Do not create duplicate work solely to produce a benchmark.

## Measure What Happened

Use `python3 scripts/usage_by_model.py --task-id current --by-agent --by-session --json` after the relevant children have finished. Record:

- artifact correctness and requirement coverage;
- main-thread context avoided;
- briefing, waiting, inspection, and rework cost;
- wall-clock effect from useful parallelism;
- uncached input, cached input, output, reasoning output, and estimated Standard credits by session;
- permission or runtime differences from the configured profiles.
- transient failures, nested fan-out, partial shared artifacts, retries, and duplicated review.

Do not treat total input tokens as direct cost without separating cached input. Do not infer causality from daily or all-history aggregates. A child's opinion that its spawn was useful is not primary evidence; judge the returned artifact, the inspection needed, and task-scoped usage.

When a child fails, inspect the shared target before counting the attempt as lost or retrying. Record recoverable artifacts separately from the missing final report. Count child-created descendants as part of the initiating route, and flag any fan-out that the parent did not explicitly authorize.

## Interpret The Roles

- Keep `Explorer` on a lower-cost model when it reliably returns compact evidence and prevents noisy discovery from entering the main context. Remove it from short tasks whose sources the main thread must inspect anyway.
- Keep `Executor` on a lower-cost model for bounded work when its output passes deterministic checks with little rework. Escalate only when unresolved judgment or failure impact exceeds the role.
- Use `Complex Executor` when the main thread has already fixed the important decisions and substantial execution still benefits from isolated deep reasoning.
- Use `Reviewer` when independent judgment can catch consequential or hard-to-verify mistakes. Do not make it an automatic final stage.

Prefer changing routing thresholds or brief quality before upgrading every role's model or reasoning effort. Change a profile only when repeated task-scoped evidence shows a role cannot meet its boundary.

## Report The Result

For each spawn, record role, runtime model and effort, purpose, outcome quality, rework, task-scoped usage, and keep/change verdict. Separate confirmed findings from one-off impressions and note that local logs omit unavailable or ephemeral sessions.
