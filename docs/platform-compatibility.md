# 平台验证矩阵

记录格式：

```text
平台 / 版本 / 日期 / OS / 安装位置 / 发现结果 / 显式调用 /
相对参考文件读取 / 材料模式输出 / 联网模式输出 /
脚本执行 / 降级行为 / 证据位置 / 未测原因
```

四个层次互不替代：**静态结构合规**（文件/路径/格式满足检查）、**宿主发现与加载**（该版本平台能找到并读取 Skill）、**行为验证**（在记录的模型/权限/工具组合下完成了指定用例）、**联网验证**（搜索、网页读取实际可用）。状态用 `passed` / `failed` / `not_tested`。

## Claude Code

- 版本：本机 Claude Code（通过本次会话所用的 harness），2026-09-03
- OS：macOS (Darwin 23.5.0, arm64)
- 安装位置：`~/.claude/skills/industry-research/`（`python3 tools/install.py --platform claude` 安装，随后用 `--replace` 覆盖了一份 2026-09-03 16:44 创建的、内容不同的旧版本，旧版本已备份到 `~/.industry-research-backups/claude-20260903T095226Z/`，未纳入本仓库）

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | `tools/check_skill.py` 通过；frontmatter `name: industry-research` 正确；相对引用全部可解析 |
| 宿主发现与加载 | passed | 安装后，当前会话的可用 Skill 列表中出现 `industry-research`（系统提示自动列出），说明 Claude Code 从 `~/.claude/skills/industry-research/` 正确发现了本 Skill |
| 显式调用 `/industry-research` | not_tested | 本次验证在非交互式 harness 中完成，未实测斜杠命令的交互式输入；发现层已确认该命令会被注册（Claude Code 文档：Skill 目录名即为命令名） |
| 自然语言自动触发 + 实际研究行为 | passed（单次抽样） | 另开一个全新、无先前上下文的子 Agent，只给出"我要在商务通话前快速了解中国协作机器人行业"这类自然语言请求，观察其是否自行发现并使用本 Skill、是否产出 report.md/evidence.json、是否做证据区分。结果记录见 `docs/validation-report.md` 的对应条目。这是一次抽样验证，不代表触发在所有措辞下都稳定 |
| 相对参考文件读取（references/、assets/） | passed | 安装后的目录结构完整（`ls` 确认 `references/`、`assets/`、`scripts/` 均已复制），子 Agent 测试中报告实际引用了 references 中的方法 |
| 材料模式输出（无联网，仅用户材料） | not_tested | 本次抽样测试子 Agent 具备联网能力，未构造"无联网"场景 |
| 联网模式输出 | passed | 子 Agent 测试中确认使用了网络搜索 |
| 脚本执行（`scripts/validate_evidence.py`） | passed | 本机直接运行验证，见 `docs/validation-report.md` 和 `examples/public-industry-case/validation.json` |
| 降级行为（无 Python） | not_tested | 未构造无 Python 的环境 |
| 证据位置 | 见 `docs/validation-report.md`；子 Agent 完整transcript 未保留在仓库中（属于运行时会话记录，不属于可公开分发的仓库内容） |

## Codex

- 安装位置（默认）：`~/.agents/skills/industry-research/`；项目级 `.agents/skills/industry-research/`
- 调用：CLI/IDE 中 `$industry-research`；ChatGPT Work 中 `@industry-research`
- 元数据：`agents/openai.yaml` 提供 UI 展示名称、简介、默认 prompt

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径、frontmatter、`agents/openai.yaml` 均符合 [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills/)（2026-09-03 核对，该 URL 会 308 重定向到 `learn.chatgpt.com/docs/build-skills`，内容一致）文档描述的格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform codex --dest <path>` 在本机测试通过（见 `tests/test_install.py`），生成的目录结构符合 Codex 文档描述的 `.agents/skills/<name>/SKILL.md` |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 | not_tested | 本次执行环境中没有可用的 Codex CLI/账号，无法实测。原因：Codex 需要独立的账号登录和运行时，本会话运行在 Claude Code harness 中，不具备该运行时 |

## OpenClaw

- 安装位置（默认，管理型目录）：`~/.openclaw/skills/industry-research/`
- 调用：`openclaw skills list` / `openclaw skills info industry-research` 确认发现；`/skill industry-research <任务>` 调用
- Git 直接安装：`openclaw skills install git:jiguang9/industry-research@v0.1.0`——该命令要求"`SKILL.md` 位于源仓库根目录"，本仓库正好符合这一结构（单 Skill、仓库根目录即 Skill 根目录），因此理论上应可用；但由于本机没有 OpenClaw 运行时，**该命令本身未实际执行验证**

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径与 SKILL.md frontmatter（`name`、`description`）符合 [docs.openclaw.ai/tools/skills](https://docs.openclaw.ai/tools/skills)（2026-09-03 核对）描述的最小格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform openclaw --dest <path>` 本机测试通过 |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 / Git 直接安装 | not_tested | 本机未安装 OpenClaw CLI，也没有可用账号/Gateway，无法实测 `openclaw skills list`、`/skill` 调用或 `openclaw skills install git:...` 命令的实际效果 |

## Hermes Agent

- 安装位置（默认 profile）：`~/.hermes/skills/industry-research/`
- 调用：让当前 Agent 列出/描述其技能确认发现后，`/industry-research <任务>`
- GitHub 直接安装：官方文档描述的格式是 `hermes skills install owner/repo/skills/<name>`，即期望仓库内有 `skills/<name>/SKILL.md` 这样的子路径。**本仓库是单 Skill、SKILL.md 位于仓库根目录，不符合这个子路径形态**，因此 `hermes skills install jiguang9/industry-research/skills/industry-research` 这类命令**不适用**，本文档不虚构一个能跑通的子路径命令。Hermes 用户应改用：`git clone` 本仓库后运行 `tools/install.py --platform hermes`，或直接用文档中的"Direct URL"方式安装单个 `SKILL.md`（`hermes skills install https://raw.githubusercontent.com/jiguang9/industry-research/main/SKILL.md`，该方式只会拉到 `SKILL.md` 本身，不含 `references/`、`assets/`、`scripts/`，因此**不推荐**，仍建议用 `tools/install.py`）

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径与 frontmatter 符合 [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)（2026-09-03 核对）描述的格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform hermes --dest <path>` 本机测试通过 |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 | not_tested | 本机没有 Hermes Agent 运行时或账号，无法实测 |

## 已知限制与后续验证计划

- 四平台中只有 Claude Code 在本次交付中完成了"宿主发现"和"行为验证"层的实测（且行为验证只有一次抽样，不代表所有措辞和场景下都稳定触发）；Codex、OpenClaw、Hermes 三个平台目前只做到了"静态结构合规"和"本项目安装脚本可用性"两层。
- 后续如果能获得 Codex/OpenClaw/Hermes 的可用账号或本地运行时，应按本文件顶部的记录格式补齐对应条目，不应把"能被 `tools/install.py` 正确安装"误报为"该平台已实测可用"。
- Windows 未在本次验证范围内；CI（`.github/workflows/ci.yml`）目前只跑 Linux 和 macOS。
