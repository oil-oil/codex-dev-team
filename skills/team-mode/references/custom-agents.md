# Custom Agent Profiles

Read this reference only when the expected custom Agent profiles or `default` dispatch guard are missing, the user asks to install or change them, or their names, models, reasoning effort, or permissions need verification. Normal task routing does not require this file.

## Run Onboarding Once

Do not inspect these files or repeat onboarding during each Team Mode task. The active `spawn_agent.agent_type` choices and descriptions are sufficient readiness evidence: when the four working profiles are selectable and `default` is described as the dispatch guard, continue normal routing without loading this reference again.

Run onboarding only for a first installation, a missing or mismatched profile, an explicit verification request, or a user-requested move, disable, restore, or customization. Configuration changes require user authorization. After setup or repair, report the installed scope and paths, all role-to-model mappings, the guard's behavioral effect, restart or new-task requirements, and the reversible disable/restore instructions below.

## Confirm Runtime Availability

Current Codex releases enable subagent workflows by default. Custom profile selection still requires a runtime whose `spawn_agent` tool exposes `agent_type`; the tool surface in the active task is stronger evidence than a remembered feature flag.

If `agent_type` is missing, update or restart Codex and open a new task before testing again. Do not enable an undocumented or stale feature flag from memory. See the current [Codex subagent manual](https://learn.chatgpt.com/docs/agent-configuration/subagents.md).

When spawning, pass the exact working profile name through `agent_type`. `task_name` only labels the child thread and never selects a profile. Never omit `agent_type` or pass `default` during normal routing. Do not substitute a generic child named `explorer`, `executor`, or `reviewer` when the intended custom profile is unavailable.

## What Must Be Installed

The Skill and custom Agent profiles are separate Codex configuration surfaces. Standard onboarding installs four working profiles plus one fail-closed `default` guard; installing `team-mode` alone does not create them.

Use these exact profile names and recommended defaults:

- `Explorer`（探索者）: `gpt-5.6-luna`, `medium`, `read-only`.
- `Executor`（执行者）: `gpt-5.6-luna`, `medium`, `workspace-write`.
- `Complex Executor`（复杂执行者）: `gpt-5.6-sol`, `high`, `workspace-write`.
- `Reviewer`（复审者）: `gpt-5.6-sol`, `high`, `read-only`.
- `default`（派发哨兵）: `gpt-5.6-terra`, `low`, `read-only`; it refuses every task and tells the parent to respawn with an explicit working profile.

The guard is not a fifth working role. Codex selects it only when the parent omits `agent_type` or explicitly passes `default`. Its low-cost model minimizes the cost of a routing mistake. Each profile's explicit `model` and `model_reasoning_effort` override the parent for that child only; installing the Terra Low guard does not change a Sol XHigh main thread.

These model IDs are repository defaults verified in the intended installation. Public Codex environments may expose a different efficiency model such as `gpt-5.6-terra`. If `gpt-5.6-luna` is unavailable, ask before substituting another model; preserve the role boundary and verify the actual runtime trace after the change.

Use the canonical templates in the repository's [`agents`](https://github.com/oil-oil/codex-team-mode/tree/main/agents) directory. Do not duplicate or rewrite their developer instructions from memory.

## Choose The Scope

- Personal profiles: place the TOML files under `~/.codex/agents/`.
- Project-only profiles: place them under `<repository>/.codex/agents/`.

Keep these filenames:

- `Explorer.toml`
- `Executor.toml`
- `Complex Executor.toml`
- `Reviewer.toml`
- `default.toml`

Codex identifies a custom Agent by its `name` field. Keep the names unchanged unless the Skill routing names are updated at the same time.

## Keep Fan-Out Shallow

Keep the global nesting limit at one so the root may spawn direct children but children cannot create descendants:

```toml
[agents]
max_depth = 1
```

Current Codex releases default `agents.max_depth` to `1`; keep that default unless the user explicitly needs bounded recursive delegation. Choose `agents.max_threads` according to the runtime's available slots and resource budget rather than assuming the public default. The Skill still starts only the minimum useful number of Agents.

## Install Or Repair

1. Confirm that the user has authorized writing personal or project Codex configuration. Do not silently create global profiles just because a substantial task triggered the Skill.
2. Inspect the destination directory first. Preserve unrelated profiles. If a same-named file already exists, compare it with the template and ask before replacing user changes.
3. Copy the five canonical TOML templates to the selected Agent directory with the exact filenames above. The four named working profiles perform tasks; `default.toml` only blocks invalid dispatches.
4. Parse every file with Python `tomllib` or an equivalent TOML parser. Confirm that each contains `name`, `description`, and `developer_instructions`, plus the intended model, reasoning effort, and sandbox mode.
5. Report the final path and role-to-model mapping. Explain that a personal `default.toml` affects omitted/default subagent dispatches across the user's Codex tasks, while a project-scoped guard affects only that trusted project configuration scope.
6. Explain the reversible guard controls below. Do not disable, move, or delete anything unless the user asks.
7. If the new profiles do not appear immediately, tell the user to open a new Codex task or restart Codex.

## Explain How To Disable The Guard

The onboarding completion message must say that disabling only the guard leaves `Explorer`, `Executor`, `Complex Executor`, and `Reviewer` installed. Prefer a recoverable move outside the active `agents` directory over deletion.

For a personal installation, tell the user they can ask Codex to perform this move or run:

```bash
mkdir -p ~/.codex/agents-disabled
mv ~/.codex/agents/default.toml ~/.codex/agents-disabled/default.toml
```

For a project installation, use the corresponding `<repository>/.codex/agents/` and `<repository>/.codex/agents-disabled/` paths. Restart Codex or open a new task after moving the file. To restore strict dispatch, move `default.toml` back into the active `agents` directory and restart or open a new task again.

## Verify Availability

Installed profiles and running subagents are different things. An activity or agent-thread list normally shows only instances that have already been spawned; it does not need to show all installed profiles while they are idle.

Verify installation by checking the TOML files and their exact `name` fields. Restart Codex or open a new task before runtime checks.

First run one controlled guard self-test: deliberately omit `agent_type`, set `fork_turns="none"`, and give the child a no-tool one-line probe. This onboarding self-test is the only permitted omission. The child must ignore the probe and return exactly:

```text
DISPATCH BLOCKED: the delegated task was not executed because agent_type was omitted or set to default. Respawn with agent_type=Explorer, Executor, Complex Executor, or Reviewer.
```

The trace should show `gpt-5.6-terra` with `low` effort. Because the invalid dispatch omitted its role, retained logs may label it `subagent/unknown`; that is expected for this test. If it performs the probe instead, the guard was not loaded: stop the child, verify `default.toml`, then restart or open a new task before trying once more.

Next use a small bounded request to spawn `agent_type="Explorer"` with `fork_turns="none"`. Keep this check read-only.

Confirm the result from runtime trace data rather than the child's self-report:

- `session_meta.agent_role` is `Explorer`.
- `turn_context.model` matches the profile model.
- `turn_context.effort` matches the configured reasoning effort.
- `turn_context.sandbox_policy` shows the effective sandbox.

The active parent task's permission mode may override a child profile's TOML sandbox setting. For example, a parent running with a live `danger-full-access` override can produce an `Explorer` whose model and reasoning match the profile while its effective sandbox remains `danger-full-access`. If read-only isolation is required, start the parent task with compatible permissions and verify the child trace after spawning. Do not rely on the TOML field alone.

The same limitation applies to the `default` guard: its developer instructions make invalid routing fail closed at the Agent-behavior layer, but it is not an operating-system security boundary and does not prevent the child thread from being created.

If `spawn_agent` does not expose `agent_type`, update or restart Codex and open a new task. If trace data shows an empty or generic role, the custom profile was not selected.

If a required profile remains unavailable, tell the user which file or setting is missing. Continue in the main thread only when that still satisfies the user's request; do not silently substitute a differently configured Agent for security-sensitive or independent-review work.

## Customize Models Safely

Model availability and cost preferences may differ between Codex environments. The user may change `model` and `model_reasoning_effort` without changing the role design.

Preserve these boundaries when customizing:

- Keep `Explorer` and `Reviewer` read-only.
- Keep mutation permissions limited to the two executors.
- Keep child fan-out disabled; all standard Team Mode routing stays in the main thread.
- Keep `Reviewer` independent through the Skill's fresh-context rule.
- Keep unresolved user intent, product, editorial, architecture, and safety decisions in the main thread.
- Keep `default` as a low-cost no-work guard; never repurpose it as a general Agent.
- Ask before replacing an unavailable configured model with another model.
