---
name: deepseek-project-workers
description: Use the installed OpenCode Go DS Flash MAX drawing and project organization/move workers on Windows, with role-local recovery and Root review. Use for DS协作绘图、项目整理、退役搬迁、角色补位; general read-only source analysis uses codex-deepseek-worker.
---

# DS project workers

Codex Root controls scope, scientific definitions and acceptance; DS handles bounded presentation proposals or organization advice. Use existing programs, not an improvised unrestricted OpenCode shell. This skill instructs Codex orchestration; it is not model training and does not grant permissions.

## Setup

Windows 10/11, PowerShell 7.2+, Python 3.12+, and an authenticated OpenCode Go CLI are required. Run the bundled `scripts/Install-Workers.ps1` once; it discovers local runtimes and refuses to overwrite existing worker installations. Read [setup and jobs](references/setup-and-jobs.md) for install arguments, templates and checks. Default worker-home is `$HOME/AgentTools`; `DEEPSEEK_WORKER_HOME` or `-WorkerHome` selects another root. Login on the target computer; never copy credentials. The installer makes no model calls or global OpenCode changes.

## Route

- **Drawing (DS owns code; default for new presentation logic):** `<worker-home>/DeepSeekPlotWorker/Invoke-DeepSeekPlotAuthor.ps1`. A authors complete Python/pvpython presentation source, pauses for exact Root code approval, then renders locally; B independently reviews the actual image and code. Revisions return to A and pause for a fresh exact approval. Read `AUTHOR_WORKFLOW.md` in that worker folder for the job contract. Root owns scientific definitions/conversion and final acceptance. This is reviewed execution, not an OS sandbox. A synthetic matplotlib acceptance test does not validate every ParaView case.
- **Drawing (existing adapter compatibility):** `<worker-home>/DeepSeekPlotWorker/Invoke-DeepSeekPlotWorker.ps1`. A adjusts an approved layout; B independently sees the real preview and renderer code/parameters. At most three layout rounds, two roles per round. For its exact job schema and renderer contract read that tool's `README.md` only when needed. New logic is a code candidate for Root review before execution; the currently verified renderer is the frozen Slab displacement plot, not every temperature/composite/ParaView task.
- **Organization/moves:** `<worker-home>/DeepSeekOrganizationWorker/Invoke-DeepSeekOrganizationWorker.ps1`. Two roles for small batches; up to four for complex dependency work: A inventory/classification, B dependency check, independent C counterexamples without A/B conclusions, D integration. One logical round. Read this tool's `README.md` for the candidate/approval formats.
- **General read-only analysis:** use the original `codex-deepseek-worker` skill/runner. Its original interface remains unchanged; the specialized workers' automatic recovery must not be claimed for that old runner.

Use PowerShell 7 in a separate process. CLI model is always `opencode-go/deepseek-v4.1-flash#max`, including replacement roles. No fallback or `--auto`; do not inspect credentials or alter global configuration.

## Dispatch

Read the repository's local instructions and active entry. Build a narrow job with exact immutable inputs, task, scope and wall budget. Worker artifacts belong outside the scientific repository by default. Root owns scientific C++/Tcl/Python changes, diagnostic/launcher code and dependency decisions. Native execution profiles follow the repository rules; the originating Slab project uses Terra-high for released execution and Luna-low for monitoring; other repositories retain their own authorized profiles. DS does not replace Root's scientific review.

External DS does not inherit Codex skills. Before research drawing, use installed skill_routes.py to build a new exact-hash job for the actual task: civil-curves (time histories, hysteresis, IDA, fragility, storey/cost figures), civil-panels (multi-panel data), civil-image-plate (morphology), civil-paraview (FE rendering), scientific-python (other data), editable-schematic or academic-diagram. Civil routes load nature-figure core, Python backend, QA and civil profile; multi-panel and ParaView add their relevant references. Read and append other necessary references; do not load every unrelated skill. Both A and B receive the same frozen FULL texts via UTF-8 stdin; only the actual image uses the single --file flag. Read AUTHOR_WORKFLOW.md for routes/limits and inspect prompt.txt plus native stdin receipts. Naming a skill is not loading, and loading guidance does not prove its helpers ran. Task-specific axes, physical definitions, chosen style and target venue override unrelated example defaults.

For a new plot, freeze input files/hashes, units and input_contract; use the author entry `-Mode start -JobFile <absolute job>`. Read the actual candidate source before saving its exact approval template as a separate approval, then `-Mode resume -Run <run> -ApprovalFile <approval>`. Every changed program needs internal Root review. Do not ask the user again for that internal release. Keep approved rendering libraries/environment stable; executable hashes do not freeze all imported packages. For compatibility parameter adjustment, supply the approved adapter/schema and use the original entry with `-JobFile <absolute job>`. Preserve every scientific observation/vertex and the user-selected temperature scenario. Root inspects actual final-size images plus input/source correspondence; a vision probe proves image delivery, not figure correctness.

For organization, give explicit candidate paths, protected prefixes and Root's actual dependency-review facts. Unknown dependencies => hold. Do not infer retirement from old dates, duplicate contents, missing text references or zero-byte logs. Invoke the organization entry with `-Mode plan -JobFile <absolute job>`; inspect A/B/C/D disagreements and actual plan. D cannot expand A's move scope or bypass blockers.

User authorization persists; do not ask again merely because an internal Root release is required. After Root reviews the concrete authorized plan, create its exact plan-hash/ID approval and run `-Mode dry-run`, then `-Mode apply` with that `-PlanFile`/`-ApprovalFile`. No overwrite, deletion, scientific solve or Git push is implied. Only move to the dedicated repository trash; moving does not release disk space. File-operation failures are not automatically retried. Explicit rollback requires an unchanged complete move and vacant source paths.

## Automatic role replacement

Upstream truncation, recognized transient network/HTTP failures and a confirmed owned request timeout trigger **only that role's** fresh-session replacement. Completed roles retain their receipts; no whole-workflow restart. Each failed attempt retains logs and `attempt_failure.json`; replacement folders use `_retry02`/`_retry03`, and `role_attempts.jsonl` records the sequence.

Defaults: `role_retries=2` (three attempts including initial), `max_replacements=4` across the job; retries remain inside the original wall/output limits with short backoff. These count replacement attempts, not additional logical roles or layout rounds. Do not reset caps by renaming the job or silently increase budgets. Exhausted budgets return original evidence to Root.

Model/identity mismatches, unexpected tools, changed inputs/config, authentication/permission/quota problems, malformed complete handoffs, scientific/QA failures and uncertain process cleanup are not transient recovery cases. Root diagnoses them. A failed review may request a bounded layout revision; that is different from an interrupted-role replacement. Never apply role retry to a move, compilation or OpenSees/PDE solve.

Author v1.2 supports automatic replacement after a verified owned model-request timeout. The native helper creates the process suspended, assigns a non-breakaway Windows Job Object, then resumes it. On timeout it terminates that entire private CLI/server tree and requires zero active processes before replacing only the failed role. Full UTF-8 stdin is supplied as an inherited file handle with EOF; delivery does not prove model consumption. Preserve successful roles, failures and the original retry/wall/output caps. Session-export timeouts, output-limit terminations, rendering failures and uncertain cleanup do not trigger fresh inference. Legacy direct-process-only receipts remain ineligible. Legacy adapter and organization behavior is unchanged.

## Silent execution monitoring

Author v1.3 uses silent local progress snapshots (5s) and heartbeat records (600s), with no inference calls or periodic user messages. New author/reviewer requests use a 2400s (40-minute) upper bound and an explicit finite whole-job budget (supported maximum14400s). Read read_author_progress.py --run RUN for a compact status. Check timestamp freshness and native receipts: local liveness/step_start is not remote-model progress; missing output means progress unknown. Monitoring does not change watchdogs, retry caps or acceptance gates. Historical jobs retain their frozen settings; legacy adapter and organization modes keep their own budgets.

## Collaboration practice

Read [collaboration practice](references/collaboration-practice.md) when preparing drawing data/contracts, diagnosing latency or assessing capability. For new author jobs omitted request/wall limits default to2400/10800s; explicit diagnostic caps remain unchanged. Use optional Root-owned `data_brief` (schema, units, reference state, counts/ranges/examples) for frozen input names. Previews never replace runtime observations. A authors source; B reviews actual images; the appended phase contract scopes full guidance to the current role. `stage_summary.json` separates source/release/execution/QA/independent review and Root record. Do not treat missing output as a proven hang, a short echo as coding proof, or a one-case success as universal readiness.

## Review and handoff

First read compact native exit/result status, then the successful role receipts and the attempt ledger if replacements occurred. Organization success is `proposed_pending_root_review` or `moved_pending_root_review`; drawing success is `candidate_ready_pending_root_review`. Root reads actual source/diff, representative raw sessions/data, tests and version correspondence before accepting. A successful invocation or model review is not scientific acceptance.

Batch candidate byte checks locally and return counts/anomalies. Avoid repeated whole-project hashes and long logs in model context. Check actual runnable dependencies separately: Python `-B` prevents cache writes but can still read pyc; retiring bytecode needs true source-only loading or an equivalent discriminating check. Keep historical receipts/manifests unchanged and archive replaced worker code with the upgrade record.
