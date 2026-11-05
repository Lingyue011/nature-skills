# DS 自编绘图程序 worker（author-v1）

安装后入口：`<worker-home>/DeepSeekPlotWorker/Invoke-DeepSeekPlotAuthor.ps1`。
适用于有明确数据契约的科研绘图任务；呈现作者和独立审图均固定使用
`opencode-go/deepseek-v4.1-flash#max`。旧 `Invoke-DeepSeekPlotWorker.ps1`
保留为已冻结 adapter 的参数调整入口。

## 分工和执行

1. Root 冻结科学数据、单位、参考状态和输入契约，选择 Python 或 pvpython。
2. DS A 自己编写完整呈现程序；worker 保存源码，停在 `pending_code_review`。
3. Root 阅读实际源码、依赖及其读写效果。审查通过后，将精确的
   `approval_template.json` 保存为独立批准文件。此为内部发布，不重复向用户询问。
4. resume 运行已审源码，DS B 在独立会话查看真实预览、源码与 QA，提出修改或接受。
5. 若需修改，DS A 根据反馈编写下一版，重新停在代码审查；最多三轮。
6. `candidate_ready_pending_root_review` 后 Root 检查最终图及数据对应关系，记录验收。

Root 不代写日常布局、相机、色标、图版逻辑。DS 不改模型、求解器、科学量定义或原始数据。
程序接口为 `--inputs DIRECTORY --output NEW_DIRECTORY`；须仅在输出目录生成
`figure.png`、`preview.png`、`qa.json`（含布尔 `passed` 及有意义的核查项）。
程序可按契约生成附属呈现文件，但不得启动求解器、shell、subprocess、网络或安装包。

## JSON 任务字段

|字段|内容|
|---|---|
|`inputs`|1–12 个普通文件绝对路径；文件名唯一，总计至多 24 MiB|
|`approved_sha256`|上述每个绝对路径对应的小写 SHA256|
|`renderer_exe`, `renderer_sha256`|明确的 Python/pvpython `.exe` 路径和 SHA256|
|`task`|呈现目的与要求，最多 12000 字符|
|`input_contract`|文件结构、物理量、单位、允许库及验收要求，最多 12000 字符|
|`author_preview`|可选；上述已批准输入中的一个图片文件名，供 A 首轮查看|
|`figure_profile`|见下表；`generic` 仅供不需要领域技能的明确任务|
|`guidance_delivery`|路由任务为 `stdin`，避免 Windows 命令行长度限制；旧小任务可用 `inline`|
|`guidance_files`|Root 选定的 skill/参考正文绝对路径，最多 16 文件；stdin 模式合计至多 192 KiB，inline 至多 24000 bytes|
|`approved_guidance_sha256`|上述指导文件绝对路径对应的 SHA256；同时冻结原件与副本|
|`max_rounds`|1–3|
|`turn_seconds`|30–600|
|`wall_seconds`|120–2400；包含 Root 审查暂停时间，不跨进程重置|
|`render_seconds`|10–180；渲染不自动重试|
|`role_retries`|0–2，默认 2；仅已识别且无强制终止的上游瞬时失败|
|`max_replacements`|0–4，默认 4；只重试已识别的上游瞬时错误|

```powershell
& $pwsh -NoProfile -File "$worker/Invoke-DeepSeekPlotAuthor.ps1" -Mode start -JobFile $job
# Root 读实际 candidate.py 后保存准确批准文件，再运行：
& $pwsh -NoProfile -File "$worker/Invoke-DeepSeekPlotAuthor.ps1" -Mode resume -Run $run -ApprovalFile $approval
```

入口读取同目录 `worker-config.json`，其 runtime 路径由安装器提供；不保存凭据。
科研数据之外的合成验收任务可用于检查本机 transport，不表示所有算例已验证。

## 按任务加载技能，不限 ParaView

外部 DS **不会自动继承 Codex 加载的 skill**。Root 依据任务选择以下路由，
使用 `skill_routes.py` 将完整资源路径/hash 写入新的任务文件；缺少资源时拒绝启动。

|路由|适用工作|实际加载|
|---|---|---|
|`scientific-python`|通用科研数据图|nature-figure 主技能、manifest、contract、stance、Python 后端、QA|
|`civil-curves`|时程、滞回、IDA、易损性、楼层响应、计算成本等数据图|通用科研数据图规则 + 土木工程 profile|
|`civil-panels`|多面板论文数据图|civil-curves + 多面板证据架构|
|`civil-image-plate`|试验/有限元现象图片组合|土木 profile 中的形态图片分支 + 多面板规则；不套曲线图例|
|`civil-paraview`|有限元变形渲染与图版|civil-curves + civil-paraview-figures 主技能及 recipes|
|`editable-schematic`|可编辑流程、方法和机制图|nature-figure 核心 + vector schematic workflow/style|
|`academic-diagram`|适用的学术架构/系统图|academic-plotting 主技能；不强行套用 ML 术语或配色|

```powershell
& $python "$worker/skill_routes.py" --job $baseJob --output $newJob --profile civil-panels
```

默认读取用户级 `.codex/skills`；`--skill-root` 可指定其他技能根目录。
路由不执行 helper，不调用模型，不改原任务文件。需要额外参考/模板时 Root 阅读后追加到
guidance_files 并更新批准 hash。已选 Python/pvpython 的现有 author 入口不冒称支持 R 执行。

worker 将这些指导文件的**全文**分别写进 A 与 B 的实际提示词，记录文件名/hash，
每次修改仍传递同一份冻结指导；不是只告诉 DS 一个它无法读取的路径或 skill 名称。
任务目录 `guidance/` 和各轮 `prompt.txt` 可审计实际送达内容。
长提示词由专用 author_native.ps1 经 UTF-8 stdin 传给 CLI；`--file` 只传一张真实图片。
不使用重复 `--file` 发送多份技能，防止 CLI 单值标志覆盖图片。stdin 提示词也有明确长度上限。
算例特定轴向、单位和科学定义优先于 skill 中的其他算例示例。
需要额外 helper 时，Root 另行选定并核验其实际调用，不能因提示词提到就声称已运行。
普通曲线图使用适用的通用绘图指导，不能机械套用 ParaView 的侧视/轴向约定。

## 可追溯性与限制

冻结原文件、副本和目录成员，绑定源码、job、controller、pwsh、OpenCode 和 renderer
可执行文件的 hash；每轮保存批准、模型身份、session、渲染日志、机器 QA 和审图反馈。
审图附带仅出现在图片里的随机码，以核实图片送达。随机码识别正确不等于科学内容正确。
同一 run 独占锁；中断的执行或终态不能自动重放；失败证据保留。

这是**经 Root 审查代码后执行的流程，不是操作系统沙箱**。Python 包、DLL、用户环境
未全部作 hash 冻结；Root 须核对实际导入与环境，不能把 syntax check 或批准 JSON 当作安全证明。
程序运行有时限和日志上限，但这些机制不能阻止已执行代码的任意文件副作用。
worker 不为模型开放原生编辑、shell 或子 agent 工具。

author 专用 helper 保存 stdin 写入/EOF 与直接进程退出状态；这不证明所有后代已清理。
因此任何超时或强制结束均停止并交 Root 检查，**不自动 replacement**；不沿用旧入口对
owned timeout 的恢复假设。stdin 送达或退出状态未确认，即使附带 HTTP/网络错误也不重试。

本目录包含扩展源码与测试；安装器复制完整 runtime 到所选 worker-home，可供各项目调用。
离线测试不会调用模型；真实验收记录单独保存，不能以 mock 测试冒充真实 DS 闭环。
