<p align="right">
  <a href="./README.md">English</a> · <strong>简体中文</strong>
</p>

<p align="center">
  <img src="./assets/readme/agent-map.svg" width="100%" alt="四个角色化的 Dev Team Agent 分别负责代码探索、明确修改、复杂实现和独立复审，主线程负责带队与验收。">
</p>

`dev-team` 是一个 Codex Skill。它会把真实仓库里的开发工作分配给四个职责明确的自定义 Agent，但需求理解、范围控制、结果验证和最终交付仍然由主线程负责。

它的出发点很简单：只有在能够减少上下文噪音或节省等待时间时才委派。子 Agent 不是必须走完的流水线，也不应该复制整段长对话，更不能让代码的实现者代替独立复审。

## 四个专注的角色

- **Explorer · Luna Medium · 只读**：理解仓库、追踪调用链、定位根因和梳理影响范围，不修改文件。
- **Executor · Luna Medium · 可写**：处理目标明确、范围局部、风险较低，而且可以直接验证的修改。
- **Complex Executor · Sol High · 可写**：主线程冻结行为契约和验证方案之后，负责复杂但边界明确的实现。
- **Reviewer · Sol High · 只读**：独立检查正确性、回归风险、安全边界和测试遗漏。

很小的修改由主线程直接完成。未解决的需求、架构与安全决策、数据契约和最终验收也始终留在主线程。

## 上下文也是成本

子 Agent 默认使用 `fork_turns="none"`。它们不会继承整段历史对话，而是收到一份精简的任务包，其中只包含仓库路径、工作范围、冻结后的行为契约、验收标准、权限和必要检查。

`Reviewer` 更严格：它永远不能继承历史对话。它只能看到当前待审内容和中立的行为契约，不能看到之前的讨论、实现理由、作者或模型、怀疑的问题和预期结论。

并行可以减少等待时间，但不会自动减少 token。`dev-team` 默认只启动一个 Agent，只有任务确实存在互不依赖的切片时才并行。

## 安装

Skill 和四个自定义 Agent 需要分开安装。

### 第一步：安装 Skill

```bash
npx skills add oil-oil/codex-dev-team
```

也可以直接告诉 Agent：

```text
安装这个 Skill：https://github.com/oil-oil/codex-dev-team
```

### 第二步：创建四个自定义 Agent

> **为什么还需要这一步：** Skill 安装工具只会安装 `skills/dev-team`，而 Codex 自定义 Agent 的配置位于单独的 `~/.codex/agents` 目录。安装 Skill 不会自动创建这些 Agent。

把下面整段提示词复制给 Codex：

```text
请为 dev-team Skill 配置它需要的四个 Codex 自定义 Agent。

来源仓库：
https://github.com/oil-oil/codex-dev-team

请执行以下操作：
1. 读取仓库 /agents 目录中的四个 TOML 模板。
2. 如果 ~/.codex/agents 不存在，请创建它。
3. 把模板复制到这个目录，并保留以下准确文件名：
   - Explorer.toml
   - Executor.toml
   - Complex Executor.toml
   - Reviewer.toml
4. 保留模板中的 Agent 名称、模型、思考程度、沙箱权限和 developer instructions，不要自行改写。
5. 不要修改或删除其他自定义 Agent、Skill、AGENTS.md 或 Codex 全局配置。
6. 写入后使用 Python 的 tomllib 验证四个文件。
7. 确认最终配置：
   - Explorer：gpt-5.6-luna，medium，read-only
   - Executor：gpt-5.6-luna，medium，workspace-write
   - Complex Executor：gpt-5.6-sol，high，workspace-write
   - Reviewer：gpt-5.6-sol，high，read-only
8. 最后告诉我是否需要重启 Codex 才能看到这些 Agent。
```

如果新 Agent 没有立即出现，重启 Codex 或新建一个任务即可。

## 使用

这个 Skill 允许在开发任务中自动触发，也可以明确调用：

```text
使用 $dev-team 完成这个仓库任务。很小的修改留在主线程，只有适合隔离上下文或并行的边界明确任务才委派，复杂或高风险结果需要独立复审。
```

默认路由很简单：

```text
很小、明确的修改       → 主线程
需要大量阅读代码       → Explorer
清楚、局部的修改       → Executor
边界明确的复杂实现     → Complex Executor
复杂或高风险的结果     → 全新的 Reviewer
```

Reviewer 发现问题以后，主线程先确认问题是否成立。很小的修复由主线程完成；边界清楚的修复交给 `Executor`；复杂修复交给 `Complex Executor`。复杂或高风险修复完成后，再交给一个使用 `fork_turns="none"` 的全新 `Reviewer`。

## 自定义模型

仓库里的模型配置来自这套工作流最初的实践。不同 Codex 环境可用的模型可能不同，你可以修改 `agents/*.toml` 中的 `model` 和 `model_reasoning_effort`。

无论怎么修改模型，都建议保留这些原则：

- Explorer 和 Reviewer 保持只读。
- Reviewer 不继承任何历史对话。
- 产品和架构决策留在主线程。
- 主线程必须检查真实 Diff 和测试结果，不能直接相信子 Agent 自报完成。

## 仓库结构

```text
codex-dev-team/
├── agents/                  # 四个 Codex 自定义 Agent 模板
├── assets/readme/           # GitHub-safe SVG 视觉素材
├── skills/dev-team/         # 可以安装的 Skill
│   ├── agents/openai.yaml
│   └── SKILL.md
├── LICENSE
└── README.md
```

<p align="center">
  <a href="https://github.com/oil-oil/beautify-github-readme"><img src="./assets/readme/made-with-beautify.svg" width="300" alt="README made with beautify-github-readme"></a>
</p>

MIT License
