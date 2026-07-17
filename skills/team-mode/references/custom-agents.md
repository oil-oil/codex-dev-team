# Custom Agent Profiles

Read this reference only when the expected custom Agent profiles are missing, the user asks to install or change them, or their names, models, reasoning effort, or permissions need verification. Normal task routing does not require this file.

## Enable Custom Profile Routing

Custom profile selection requires a runtime whose `spawn_agent` tool exposes `agent_type`. On current Codex CLI releases, enable the required multi-agent path persistently:

```bash
codex features enable multi_agent_v2
codex features list | rg '^multi_agent_v2'
```

Restart Codex and open a new task after changing the feature. `multi_agent_v2` is currently under development, so its interface may change.

When spawning, pass the exact profile name through `agent_type`. `task_name` only labels the child thread and never selects a profile. Do not substitute a generic child named `explorer`, `executor`, or `reviewer` when the intended custom profile is unavailable.

## What Must Be Installed

The Skill and custom Agent profiles are separate Codex configuration surfaces. Installing `team-mode` does not create the four profiles.

Use these exact profile names and recommended defaults:

- `Explorer`（探索者）: `gpt-5.6-luna`, `medium`, `read-only`.
- `Executor`（执行者）: `gpt-5.6-luna`, `medium`, `workspace-write`.
- `Complex Executor`（复杂执行者）: `gpt-5.6-sol`, `high`, `workspace-write`.
- `Reviewer`（复审者）: `gpt-5.6-sol`, `high`, `read-only`.

Use the canonical templates in the repository's [`agents`](https://github.com/oil-oil/codex-team-mode/tree/main/agents) directory. Do not duplicate or rewrite their developer instructions from memory.

## Choose The Scope

- Personal profiles: place the TOML files under `~/.codex/agents/`.
- Project-only profiles: place them under `<repository>/.codex/agents/`.

Keep these filenames:

- `Explorer.toml`
- `Executor.toml`
- `Complex Executor.toml`
- `Reviewer.toml`

Codex identifies a custom Agent by its `name` field. Keep the names unchanged unless the Skill routing names are updated at the same time.

## Install Or Repair

1. Confirm that the user has authorized writing personal or project Codex configuration. Do not silently create global profiles just because a substantial task triggered the Skill.
2. Inspect the destination directory first. Preserve unrelated profiles. If a same-named file already exists, compare it with the template and ask before replacing user changes.
3. Copy the four canonical TOML templates to the selected Agent directory with the exact filenames above.
4. Parse every file with Python `tomllib` or an equivalent TOML parser. Confirm that each contains `name`, `description`, and `developer_instructions`, plus the intended model, reasoning effort, and sandbox mode.
5. Report the final path and role-to-model mapping. If the new profiles do not appear immediately, open a new Codex task or restart Codex.

## Verify Availability

Installed profiles and running subagents are different things. An activity or agent-thread list normally shows only instances that have already been spawned; it does not need to show all installed profiles while they are idle.

Verify installation by checking the TOML files and their exact `name` fields. After opening a new task, use a small bounded request to spawn `agent_type="Explorer"` with `fork_turns="none"`. Keep the first check read-only.

Confirm the result from runtime trace data rather than the child's self-report:

- `session_meta.agent_role` is `Explorer`.
- `turn_context.model` matches the profile model.
- `turn_context.effort` matches the configured reasoning effort.
- `turn_context.sandbox_policy` shows the effective sandbox.

The active parent task's permission mode may override a child profile's TOML sandbox setting. For example, a parent running with a live `danger-full-access` override can produce an `Explorer` whose model and reasoning match the profile while its effective sandbox remains `danger-full-access`. If read-only isolation is required, start the parent task with compatible permissions and verify the child trace after spawning. Do not rely on the TOML field alone.

If `spawn_agent` does not expose `agent_type`, restart Codex and open a new task after enabling `multi_agent_v2`. If trace data shows an empty or generic role, the custom profile was not selected.

If a required profile remains unavailable, tell the user which file or setting is missing. Continue in the main thread only when that still satisfies the user's request; do not silently substitute a differently configured Agent for security-sensitive or independent-review work.

## Customize Models Safely

Model availability and cost preferences may differ between Codex environments. The user may change `model` and `model_reasoning_effort` without changing the role design.

Preserve these boundaries when customizing:

- Keep `Explorer` and `Reviewer` read-only.
- Keep mutation permissions limited to the two executors.
- Keep `Reviewer` independent through the Skill's fresh-context rule.
- Keep unresolved user intent, product, editorial, architecture, and safety decisions in the main thread.
- Ask before replacing an unavailable configured model with another model.
