# DeepSeek Project Workers

[中文说明](README.md)

## Capabilities

Windows OpenCode Go DS Flash MAX workers and a user-level skill.
DS A writes complete presentation code; Root reviews its effects before local execution.
Independent DS B inspects the real image, code and QA. Revisions return to A and require
a fresh exact-code release. Root accepts the final figure. The legacy frozen-adapter entry remains.
Organization retains A/B or A/B/C/D advice, exact plans and deterministic move tools.

## Installation and use

Requires PowerShell 7.2+, Python 3.12+, native OpenCode V2 and a Go login on the target computer.

```powershell
python -m pip install -r .\skills\deepseek-project-workers\requirements.txt
pwsh -NoProfile -File .\skills\deepseek-project-workers\scripts\Install-Workers.ps1
```

Workers default to `$HOME/AgentTools`; skills to `$CODEX_HOME/skills` or `$HOME/.codex/skills`.
The installer refuses existing workers. Upgrade into a fresh `-WorkerHome`, validate, then switch;
preserve historical jobs and local configuration. Invoke `$deepseek-project-workers` from other chats;
task context and data authorization remain project-specific.

`skill_routes.py` selects scientific data, civil curves, panels, morphology plates, ParaView,
editable schematics or academic diagrams. Full installed skill texts and references are hash-frozen
and sent to both roles through UTF-8 stdin; one image attachment enables actual visual verification.
Install the selected route's `nature-figure`, civil profile, `civil-paraview-figures` or
`academic-plotting` resources separately in the selected skill root. Missing resources stop the job;
the worker does not silently substitute another skill or change scientific data.

See [setup and jobs](references/setup-and-jobs.md) and
[author workflow](scripts/runtime/plot/AUTHOR_WORKFLOW.md) for exact contracts.

## Boundaries and validation

The model is fixed to `opencode-go/deepseek-v4.1-flash#max`. Root owns scientific definitions,
data conversion, execution review and acceptance. Reviewed code execution is not an OS sandbox;
libraries, DLLs and environment are not fully frozen. Author v1.2 replaces verified owned request timeouts; it stops on unverified termination,
or unconfirmed stdin/exit; no replacement follows those failures. Other recognized transient upstream
failures retain two replacements per role, four per job and unchanged wall/output budgets.
Moves and solves are never automatically retried. No implicit deletion, scientific source edits or Git push.

This release passed 23 author/legacy plotting tests and six existing recovery tests.
Live OpenCode V2.2.5 checks covered DS-authored code, local plotting and independent review;
a separate probe delivered eight full guidance resources (about 92k characters) plus a real image.
Mocks and delivery probes do not validate arbitrary scientific figures or live multi-round iteration.
Only source and synthetic tests are distributed: no research data, sessions, images, credentials or local runtime config.


## v1.2 timeout recovery update

Author mode now uses suspended launch and a non-breakaway Windows Job Object. A timed-out model request can be replaced automatically only after its private CLI/server tree has zero active processes. Defaults remain two replacements per role and four per job within original wall/output budgets. Session-export/render/output-limit/identity/permission failures do not start new inference. Source approval and independent real-image review remain mandatory. Tests: 18 author-state tests and 3 real Windows process tests passed; these are not evidence of live scientific-figure acceptance. This section supersedes the older author-timeout exception above.


## Author v1.3 silent monitoring

Author v1.3 uses silent local progress snapshots (5s) and heartbeat records (600s), with no inference calls or periodic user messages. New author/reviewer requests use a 2400s (40-minute) upper bound and an explicit finite whole-job budget (supported maximum14400s). Read read_author_progress.py --run RUN for a compact status. Check timestamp freshness and native receipts: local liveness/step_start is not remote-model progress; missing output means progress unknown. Monitoring does not change watchdogs, retry caps or acceptance gates. Historical jobs retain their frozen settings; legacy adapter and organization modes keep their own budgets.


## Author v1.4 collaboration contracts

New author jobs support bounded Root-reviewed data_brief, phase-specific A/B contracts, default40min requests and separate stage_summary.json. Full selected skill delivery, exact source release, actual-image review and Root acceptance remain. Read references/collaboration-practice.md (from the skill root) for tested lessons and their limits. Historical runs are preserved.
