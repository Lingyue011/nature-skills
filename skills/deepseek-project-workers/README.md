# DeepSeek Project Workers

[English](README_EN.md)

## 能力

Windows 上的 OpenCode Go DS Flash MAX worker 与用户级 skill。
绘图由 DS A 自写完整呈现程序，Root 读审后本地执行，DS B 独立看真实图、源码与 QA；
需要修改时回到 A，每版代码重新审查，最终由 Root 验收。原冻结 adapter 参数入口保留。
项目整理沿用 A/B 或 A/B/C/D 分工、精确清单和确定性移动工具。

## 安装与使用

需要 PowerShell 7.2+、Python 3.12+、原生 OpenCode V2 和本机完成的 Go 登录。

```powershell
python -m pip install -r .\skills\deepseek-project-workers\requirements.txt
pwsh -NoProfile -File .\skills\deepseek-project-workers\scripts\Install-Workers.ps1
```

默认 worker 位于 `$HOME/AgentTools`，skill 位于 `$CODEX_HOME/skills` 或 `$HOME/.codex/skills`。
安装器不覆盖旧安装；升级选新 `-WorkerHome`，核验后切换，保留历史运行与本机配置。
跨对话调用 `$deepseek-project-workers`；任务内容和数据授权遵循各项目规则。

使用 `skill_routes.py` 按任务选择通用数据图、土木曲线、多面板、形态图片、ParaView、
可编辑示意图或学术架构图。路由读取本机已安装技能的完整正文和引用资源，冻结 hash，
全文经 UTF-8 stdin 发送给作者和审图角色，单个图片附件用于真实视觉核验。
相关 `nature-figure`、土木 profile、`civil-paraview-figures`、`academic-plotting`
须另行安装于所选 skill root；缺少所选路由的资源时停止，不自动换技能或修改数据。

完整字段见[安装与任务](references/setup-and-jobs.md)和
[作者工作流](scripts/runtime/plot/AUTHOR_WORKFLOW.md)。

## 边界与验证

固定模型 `opencode-go/deepseek-v4.1-flash#max`。Root 保留科学定义、数据转换、
执行代码审查和最终验收。程序执行不是 OS 沙箱，导入库/DLL/环境未全部冻结。
author 模式超时、强制终止或 stdin/退出未确认均停止，不自动重试；可识别的其他上游
瞬时失败仍受每角色 2 次、任务总计 4 次 replacement 和原 wall/output 预算限制。
整理移动和科研求解不自动重试，不默认授予删除、科研源码修改或 Git 推送权限。

本版 author 与兼容绘图协议 23 项离线测试通过，既有角色恢复 6 项通过。
OpenCode V2.2.5 实测 DS 自写程序/本地绘图/独立审图；另测 8 份完整指导（约 9.2 万字符）
和真实图片同次送达。离线 mock 和交付探针不证明任意科研图件或多轮实际迭代已通过验收。
发布包仅含源码与合成测试，不含真实科研数据、会话、图片、凭据或本机 runtime 配置。
