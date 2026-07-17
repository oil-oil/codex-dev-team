<p align="right">
  <strong>English</strong> · <a href="./README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="./assets/readme/agent-map.svg" width="100%" alt="Four character-driven Dev Team agents divide exploration, clear fixes, complex implementation, and independent review while the main thread leads and verifies the work.">
</p>

`dev-team` is a Codex Skill for coordinating four custom development agents. The main thread leads the task, keeps unresolved decisions, and verifies the final result; subagents take on work that benefits from focused context, lower cost, or safe parallelism.

It is a routing guide, not a mandatory pipeline.

## The team

- **Explorer（看代码小子）· Luna Medium · read-only** — explores code, schemas, APIs, logs, and configuration without editing files.
- **Executor（写代码小子）· Luna Medium · workspace-write** — handles clear, localized, low-risk implementation with deterministic checks.
- **Complex Executor（写难代码小子）· Sol High · workspace-write** — handles substantial but bounded implementation.
- **Reviewer（Review 小子）· Sol High · read-only** — independently reviews stable changes, plans, and test strategies.

Luna keeps routine exploration and implementation economical. Sol is reserved for complex execution and independent review, where missing an important detail costs more.

## How routing works

- Non-trivial discovery goes to `Explorer`; the main thread can wait for its result instead of repeating the same exploration.
- After discovery, the main thread chooses whether to implement directly or delegate based on context, cost, risk, and coordination value.
- Reuse an Explorer or executor when its existing knowledge of the same task, business area, or subsystem remains useful. Start fresh when that context is stale, noisy, or could bias judgment.
- Start every new `Reviewer` with no inherited conversation. It sees the artifact and neutral requirements, not the previous debate or expected verdict.
- Parallelize only genuinely independent work. Keep one writer per shared worktree.
- The main thread inspects the real diff and verification output before accepting delegated work.

## Install

Install the Skill:

```bash
npx skills add oil-oil/codex-dev-team
```

The four custom Agent profiles are separate from the Skill. Copy the TOML templates in [`agents/`](./agents) to `~/.codex/agents/` for personal use or `<repository>/.codex/agents/` for one project.

See [Custom Agent Profiles](./skills/dev-team/references/custom-agents.md) for exact filenames, safe installation, validation, repair, and model customization. Open a new Codex task or restart Codex if newly installed profiles do not appear immediately.

## Use

The Skill can trigger automatically for substantial development work, or you can invoke it directly:

```text
Use $dev-team for this repository task. Delegate non-trivial discovery to Explorer, then choose implementation ownership based on context, cost, risk, and coordination value. Independently review complex or high-risk results.
```

You do not need to name every agent yourself. The main thread selects the smallest useful team and remains responsible for the combined result.

## Customize

You can change `model` and `model_reasoning_effort` in `agents/*.toml`. Preserve the role boundaries: Explorer and Reviewer stay read-only, implementation permissions remain with the executors, new reviews use fresh context, and final acceptance stays with the main thread.

## Repository layout

```text
codex-dev-team/
├── agents/                  # Four custom Codex Agent templates
├── assets/readme/           # GitHub-safe SVG visuals
├── skills/dev-team/         # Installable Skill
│   ├── agents/openai.yaml
│   ├── references/custom-agents.md
│   └── SKILL.md
├── LICENSE
└── README.md
```

<p align="center">
  <a href="https://github.com/oil-oil/beautify-github-readme"><img src="./assets/readme/made-with-beautify.svg" width="300" alt="README made with beautify-github-readme"></a>
</p>

MIT License
