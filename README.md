# 进化论 Agent Evolution Kit

`agent-evolution-kit` 是一个隐私安全的 Python CLI 工具，用来把本机 agent 历史记录整理成“行为层进化建议”。

这里的“进化”不是训练模型权重，而是从 Codex、Claude Code 或通用 JSONL 历史里提炼稳定偏好、失败模式、工具选择规律和安全边界，再生成可审阅的建议与批注文档。

## 它做什么

- 扫描配置允许的本机 agent 历史来源。
- 只输出统计和脱敏后的建议，不保存原始聊天。
- 生成“建议 + 批注”一一对应的 Markdown。
- 写入审阅文档时创建本地 before/after 快照。
- 支持 Windows 和 macOS 的定时任务生成。
- 支持电脑错过定时运行后，在下次启动或触发时补跑。

## 它不做什么

- 不训练模型权重。
- 不保存原始聊天、原文证据、token、cookie、密码或私钥。
- 不自动修改 `AGENTS.md`、`CLAUDE.md` 或其他全局 agent 配置。
- 不自动发送飞书/Lark 消息、邮件、日程、文档或任务。
- 不默认写入任何云端系统。

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
agent-evolve --help
agent-evolve init --config agent-evolution.toml
agent-evolve scan --config agent-evolution.toml
agent-evolve run --config agent-evolution.toml
agent-evolve validate --config agent-evolution.toml
pytest
```

macOS / Linux 可使用：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
agent-evolve --help
agent-evolve init --config agent-evolution.toml
agent-evolve scan --config agent-evolution.toml
agent-evolve run --config agent-evolution.toml
agent-evolve validate --config agent-evolution.toml
pytest
```

## 常用命令

```bash
agent-evolve init
agent-evolve scan
agent-evolve run
agent-evolve validate
agent-evolve catch-up
agent-evolve install-schedule --os windows
agent-evolve install-schedule --os mac
agent-evolve doctor
```

命令说明：

- `init`：生成默认配置文件。
- `scan`：只读扫描配置来源，输出来源数量和观察数量。
- `run`：生成审阅 Markdown、状态文件和本地快照。
- `validate`：检查审阅文档是否存在缺批注、原文证据或敏感内容。
- `catch-up`：如果距离上次成功运行超过配置间隔，则补跑一次。
- `install-schedule`：打印 Windows Task Scheduler 命令或 macOS LaunchAgent plist。
- `doctor`：检查配置文件和启用的来源数量。

## 配置文件

默认配置文件名是 `agent-evolution.toml`。

核心字段：

```toml
[workspace]
review_root = "./review"
snapshot_repo = "./snapshot-repo"
state_dir = "./state"

[privacy]
store_raw_messages = false
include_evidence_blocks = false
redact_local_paths = true
redact_private_contacts = true

[schedule]
interval_hours = 72
catch_up_on_boot = true
```

默认来源包括：

```toml
[[sources]]
name = "codex"
path = "~/.codex/sessions"
enabled = true

[[sources]]
name = "claude-code"
path = "~/.claude/projects"
enabled = true

[[sources]]
name = "generic-jsonl"
path = "./sample-history"
enabled = false
```

## 定时运行

Windows：

```powershell
agent-evolve install-schedule --os windows --config .\agent-evolution.toml
```

macOS：

```bash
agent-evolve install-schedule --os mac --config ./agent-evolution.toml
```

生成的定时任务会调用：

```bash
agent-evolve catch-up --config agent-evolution.toml
```

如果电脑在计划运行时间没有开机，下一次启动或触发时会检查 `state/last_run.json`。只要距离上次成功运行已经超过 `interval_hours`，就会补跑。

## 隐私边界

默认安全策略：

- 原始聊天不落盘。
- 原文证据块不写入审阅文档。
- 常见密钥格式会被脱敏。
- 本机用户路径会被脱敏。
- 生成的 `review/`、`state/`、`snapshot-repo/` 不进入 Git。

发布仓库只包含源码、测试、模板和说明文档，不包含任何真实本机历史记录。

## 开发

项目要求 Python 3.11 或更高版本。

运行测试：

```bash
python -m pytest -p no:cacheprovider -q
```

编译检查：

```bash
python -m compileall agent_evolution tests
```

运行发布前扫描时，应重点检查：

```bash
git grep -n -E "token|cookie|password|secret|private[_-]?key|原文证据" -- .
```

测试文件中的 fake token / fake secret 是用于验证脱敏逻辑的假数据，不是真实密钥。
