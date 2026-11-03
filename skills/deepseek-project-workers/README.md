# DeepSeek Project Workers

[English](README_EN.md)

## 能力

Windows 上可安装的 OpenCode Go DS Flash MAX 协作程序和配套 skill。
绘图由 A 调整、B 独立读图审阅；整理可用 2 或最多 4 个逻辑角色交接。
上游截断时仅补位失败角色，保留成功结果、原始记录和预算。Root 保留科学定义、源码审阅和最终验收。

## 安装

需要 PowerShell 7.2+、Python 3.12+、原生 OpenCode CLI 及自行登录的 Go 账号。

```powershell
python -m pip install -r .\skills\deepseek-project-workers\requirements.txt
pwsh -NoProfile -File .\skills\deepseek-project-workers\scripts\Install-Workers.ps1
```

默认 worker 放在 `$HOME/AgentTools`，skill 放在 `$CODEX_HOME/skills` 或 `$HOME/.codex/skills`。
安装器发现本机 Python/OpenCode 路径并生成本机配置；不调用模型、不复制凭据，不覆盖既有安装。
使用 `$deepseek-project-workers` 指定工作流。完整参数见[安装与任务](references/setup-and-jobs.md)。

## 边界与验证

绘图仅执行 Root 审阅的适配器和布局 schema；整理仅生成候选 ID，由精确清单脚本移入项目 trash。
不删除，不自动重试文件移动/科研计算，不默认获得源程序修改或 Git 推送权限。
默认每角色最多 2 次补位、任务累计 4 次，仍受原墙钟/输出预算限制。

来源工作流已通过 22 项离线测试、实际四角色整理和一次模拟截断后的真实 MAX 补位。
此发布包另做路径含空格的隔离安装测试；无真实科研数据、图件、会话或账号配置。
仅支持 Windows；安装成功不等于任意科学适配器已验证。
