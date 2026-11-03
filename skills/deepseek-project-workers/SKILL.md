---
name: deepseek-project-workers
description: Use the installed OpenCode Go DS Flash MAX drawing and project organization/move workers on Windows, with role-local recovery and Root review. Use for DS协作绘图、项目整理、退役搬迁、角色补位; general read-only source analysis uses codex-deepseek-worker.
---

# DS project workers

Codex Root controls scope, scientific definitions and acceptance; DS handles bounded presentation proposals or organization advice. Use existing programs, not an improvised unrestricted OpenCode shell. This skill instructs Codex orchestration; it is not model training and does not grant permissions.

## Setup

Windows 10/11, PowerShell 7.2+, Python 3.12+, and an authenticated OpenCode Go CLI are required. Run the bundled `scripts/Install-Workers.ps1` once; it discovers local runtimes and refuses to overwrite existing worker installations. Read [setup and jobs](references/setup-and-jobs.md) for install arguments, templates and checks. Default worker-home is `$HOME/AgentTools`; `DEEPSEEK_WORKER_HOME` or `-WorkerHome` selects another root. Login on the target computer; never copy credentials. The installer makes no model calls or global OpenCode changes.

## Route

- **Drawing:** `<worker-home>/DeepSeekPlotWorker/Invoke-DeepSeekPlotWorker.ps1`. A adjusts an approved layout; B independently sees the real preview and renderer code/parameters. At most three layout rounds, two roles per round. For its exact job schema and renderer contract read that tool's `README.md` only when needed. New logic is a code candidate for Root review before execution; the currently verified renderer is the frozen Slab displacement plot, not every temperature/composite/ParaView task.
- **Organization/moves:** `<worker-home>/DeepSeekOrganizationWorker/Invoke-DeepSeekOrganizationWorker.ps1`. Two roles for small batches; up to four for complex dependency work: A inventory/classification, B dependency check, independent C counterexamples without A/B conclusions, D integration. One logical round. Read this tool's `README.md` for the candidate/approval formats.
- **General read-only analysis:** use the original `codex-deepseek-worker` skill/runner. Its original interface remains unchanged; the specialized workers' automatic recovery must not be claimed for that old runner.

Use PowerShell 7 in a separate process. CLI model is always `opencode-go/deepseek-v4.1-flash#max`, including replacement roles. No fallback or `--auto`; do not inspect credentials or alter global configuration.

## Dispatch

Read the repository's local instructions and active entry. Build a narrow job with exact immutable inputs, task, scope and wall budget. Worker artifacts belong outside the scientific repository by default. Root owns scientific C++/Tcl/Python changes, diagnostic/launcher code and dependency decisions. Native execution profiles follow the repository rules; the originating Slab project uses Terra-high for released execution and Luna-low for monitoring; other repositories retain their own authorized profiles. DS does not replace Root's scientific review.

For a plot, supply the approved adapter, schema, input files and approved hashes. Invoke the plotting entry with `-JobFile <absolute job>`. Preserve every scientific observation/vertex and the user-selected temperature scenario. Root inspects actual final-size images plus input/source correspondence; a vision probe proves image delivery, not figure correctness.

For organization, give explicit candidate paths, protected prefixes and Root's actual dependency-review facts. Unknown dependencies => hold. Do not infer retirement from old dates, duplicate contents, missing text references or zero-byte logs. Invoke the organization entry with `-Mode plan -JobFile <absolute job>`; inspect A/B/C/D disagreements and actual plan. D cannot expand A's move scope or bypass blockers.

User authorization persists; do not ask again merely because an internal Root release is required. After Root reviews the concrete authorized plan, create its exact plan-hash/ID approval and run `-Mode dry-run`, then `-Mode apply` with that `-PlanFile`/`-ApprovalFile`. No overwrite, deletion, scientific solve or Git push is implied. Only move to the dedicated repository trash; moving does not release disk space. File-operation failures are not automatically retried. Explicit rollback requires an unchanged complete move and vacant source paths.

## Automatic role replacement

Upstream truncation, recognized transient network/HTTP failures and a confirmed owned request timeout trigger **only that role's** fresh-session replacement. Completed roles retain their receipts; no whole-workflow restart. Each failed attempt retains logs and `attempt_failure.json`; replacement folders use `_retry02`/`_retry03`, and `role_attempts.jsonl` records the sequence.

Defaults: `role_retries=2` (three attempts including initial), `max_replacements=4` across the job; retries remain inside the original wall/output limits with short backoff. These count replacement attempts, not additional logical roles or layout rounds. Do not reset caps by renaming the job or silently increase budgets. Exhausted budgets return original evidence to Root.

Model/identity mismatches, unexpected tools, changed inputs/config, authentication/permission/quota problems, malformed complete handoffs, scientific/QA failures and uncertain process cleanup are not transient recovery cases. Root diagnoses them. A failed review may request a bounded layout revision; that is different from an interrupted-role replacement. Never apply role retry to a move, compilation or OpenSees/PDE solve.

## Review and handoff

First read compact native exit/result status, then the successful role receipts and the attempt ledger if replacements occurred. Organization success is `proposed_pending_root_review` or `moved_pending_root_review`; drawing success is `candidate_ready_pending_root_review`. Root reads actual source/diff, representative raw sessions/data, tests and version correspondence before accepting. A successful invocation or model review is not scientific acceptance.

Batch candidate byte checks locally and return counts/anomalies. Avoid repeated whole-project hashes and long logs in model context. Check actual runnable dependencies separately: Python `-B` prevents cache writes but can still read pyc; retiring bytecode needs true source-only loading or an equivalent discriminating check. Keep historical receipts/manifests unchanged and archive replaced worker code with the upgrade record.
