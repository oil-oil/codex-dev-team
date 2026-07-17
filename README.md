<p align="right">
  <strong>English</strong> · <a href="./README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="./assets/readme/agent-map.svg" width="100%" alt="Four character-driven Team Mode agents divide exploration, bounded execution, complex execution, and independent review while the main thread leads and verifies the work.">
</p>

`team-mode` is a Codex Skill for coordinating four custom agents across substantial development, research, analysis, planning, document, data, and content tasks. The main thread keeps unresolved decisions and verifies the final result; subagents take on work that benefits from focused context, lower cost, safe parallelism, or independent judgment.

It is a routing guide, not a mandatory pipeline.

## The team

- **Explorer（探索者）· Luna Medium · read-only** — gathers evidence across current web sources, documents, data, code, APIs, logs, and configuration.
- **Executor（执行者）· Luna Medium · workspace-write** — completes clear, bounded, low-risk work with deterministic checks.
- **Complex Executor（复杂执行者）· Sol High · workspace-write** — completes substantial but bounded work after the intended outcome and safety boundaries are clear.
- **Reviewer（复审者）· Sol High · read-only** — independently checks stable code, reports, plans, analyses, data, and other artifacts from fresh context.

Luna keeps routine exploration and execution economical. Sol is reserved for consequential execution and independent review, where missing an important detail costs more.

## How routing works

- Use Team Mode when delegation, parallel work, context isolation, lower-cost execution, or independent review has clear value.
- Team Mode may use no subagents at all. The main thread handles straightforward work when an Executor or Reviewer would add more coordination than value.
- Give non-trivial read-only discovery to `Explorer`; the main thread can wait instead of repeating the same work.
- After discovery, the main thread chooses whether to continue directly or delegate.
- Reuse an Explorer or executor while its knowledge of the same topic, system, artifact, or workstream remains useful.
- Use `Reviewer` only when fresh independent judgment has clear value, and start every new Reviewer with no inherited conversation.
- Parallelize only genuinely independent work and keep one writer per shared target.
- The main thread inspects the actual sources, artifacts, changes, and verification before accepting delegated work.

Casual conversation, simple lookups, and tasks whose coordination cost exceeds the work stay in the main thread.

## Install

Install the Skill:

```bash
npx skills add oil-oil/codex-team-mode
```

The four custom Agent profiles are separate from the Skill. Copy the TOML templates in [`agents/`](./agents) to `~/.codex/agents/` for personal use or `<repository>/.codex/agents/` for one project.

See [Custom Agent Profiles](./skills/team-mode/references/custom-agents.md) for exact filenames, safe installation, validation, repair, and model customization. Open a new Codex task or restart Codex if newly installed profiles do not appear immediately.

## Use

The Skill can trigger automatically for substantial tasks, or you can invoke it directly:

```text
Use $team-mode for this task. Start the smallest useful team and keep unresolved decisions and final acceptance in the main thread.
```

You do not need to name every agent yourself. The main thread chooses the smallest useful team and remains responsible for the combined result.

## Customize

You can change `model` and `model_reasoning_effort` in `agents/*.toml`. Preserve the role boundaries: Explorer and Reviewer stay read-only, mutation permissions remain with the executors, new reviews use fresh context, and final acceptance stays with the main thread.

## Repository layout

```text
codex-team-mode/
├── agents/                  # Four custom Codex Agent templates
├── assets/readme/           # GitHub-safe SVG visuals
├── skills/team-mode/        # Installable Skill
│   ├── agents/openai.yaml
│   ├── references/custom-agents.md
│   ├── scripts/usage_by_model.py
│   └── SKILL.md
├── LICENSE
└── README.md
```

<p align="center">
  <a href="https://github.com/oil-oil/beautify-github-readme"><img src="./assets/readme/made-with-beautify.svg" width="300" alt="README made with beautify-github-readme"></a>
</p>

MIT License
