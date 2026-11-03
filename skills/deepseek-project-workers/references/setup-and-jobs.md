# Setup and job contracts

## Other Windows computers

Clone the branch containing this skill, or copy the complete skill folder. Install its `requirements.txt`
using the intended Python 3.12+ interpreter, then run `scripts/Install-Workers.ps1` in PowerShell 7.2+.
OpenCode Go must be installed and logged in locally. Do not copy another computer's account files.
The transport was exercised with OpenCode v2.1.2's `run --standalone --format json` and `session export` API;
a different CLI release should receive a bounded probe before research use.

Installer arguments:

|Argument|Meaning|
|---|---|
|`-WorkerHome`|Worker parent; defaults to `DEEPSEEK_WORKER_HOME`, otherwise `$HOME/AgentTools`|
|`-SkillRoot`|Skill parent; defaults to `$CODEX_HOME/skills` or `$HOME/.codex/skills`|
|`-PythonPath`|Explicit Python executable; otherwise discovered locally|
|`-CliPath`|Native `opencode.exe`; npm's usual native path or PATH discovery otherwise|
|`-SkipSkill`|Install only workers; keep an already installed companion skill|
|`-CheckOnly`|Dependency/path preflight without writing files or calling a model|

An existing skill installed at the source folder itself is retained in place. Any other existing destination
is rejected before writes. Select a fresh worker root for upgrades; do not overwrite active runs.
`worker-config.json` contains local runtime paths, not credentials. Worker launchers also accept
`-Python` and `-CliPath` overrides. A cmd/ps1 OpenCode shim is not accepted as the native CLI executable.

## Drawing

```powershell
& $pwsh -NoProfile -File "$workerHome/DeepSeekPlotWorker/Invoke-DeepSeekPlotWorker.ps1" -JobFile $job
```

Root prepares a JSON job with `adapter`, `schema`, `inputs`, `approved_sha256` keyed by their actual absolute paths,
`initial_layout`, `task`, `max_rounds` (1–3), `turn_seconds` (30–600) and `wall_seconds` (120–2400).
The renderer receives `--inputs <copied input folder> --layout <layout JSON> --output <new output folder>`;
it must write `figure.png`, `preview.png`, `qa.json` with boolean `passed` and meaningful scientific/presentation QA.
Schema entries are bounded `number` or enumerated `enum` fields. DS cannot execute arbitrary generated code.
`examples/slab_displacement_adapter.py` and `layout_schema.json` document the originally validated case;
the adapter expects Test 82/FE 392 rows and its specific columns/ranges. Its datasets are deliberately absent.
Other models need their own reviewed adapter, units, acceptance definitions and schema.

## Organization

```powershell
& $pwsh -NoProfile -File "$workerHome/DeepSeekOrganizationWorker/Invoke-DeepSeekOrganizationWorker.ps1" -Mode plan -JobFile $job
```

A JSON job contains `repository`, `roles` (2 or 4), `turn_seconds` (30–600), `wall_seconds` (120–2400),
`closure_review` (Root dependency facts file), its `closure_sha256`, `protected_paths`, `task`,
and explicit `candidates` with relative POSIX `path`, boolean `eligible`, and `note`.
No recursive whole-repository cleanup is inferred: at most 200 files, 8 MiB each, regular nonlinked files only.
Keep unknown or dynamically constructed dependencies on hold. Empty logs and old dates alone are not retirement criteria.

After actual Root review, the approval JSON needs `status: root_approved_exact_move`, `plan_sha256`,
`approved_ids` in selected order and a reason. This internal evidence is not a digital signature or a new user prompt.
Invoke `-Mode dry-run`, then `-Mode apply` with the exact `-PlanFile` and `-ApprovalFile`.
The executor retains 20 GiB free space, rejects existing targets, preserves relative paths under a fresh
`trash/ds_organization_<job>` and writes a durable journal. It does not delete empty source directories.
Partial failures stop with evidence; an explicit `-Mode rollback -PlanFile ...` restores only an unchanged complete move
if source paths remain vacant. Do not apply inference retry to mutations.

## Replacement and review

Optional job keys `role_retries` (default 2; 0–3) and `max_replacements` (default 4; 0–8) bound upstream replacement.
Successful role receipts remain; the failed role uses a fresh fixed-MAX session and unchanged prompt/inputs.
No whole-workflow restart or cross-process crash recovery is introduced. Model/auth/tool/input failures are terminal.
Inspect `role_attempts.jsonl`, the successful `receipt.json`, the final result and actual source/data/image evidence.
Application-level tool policies are not an operating-system sandbox.

## Offline tests

Use a writable private TEMP/TMP. The organization hardlink fixture requires normal Windows filesystem permissions.
No command below calls a model:

```powershell
python -B -X utf8 -m unittest discover -s skills/deepseek-project-workers/scripts/runtime/plot -p test_worker.py -v
python -B -X utf8 -m unittest discover -s skills/deepseek-project-workers/scripts/runtime/organization -p test_organization.py -v
python -B -X utf8 -m unittest discover -s skills/deepseek-project-workers/scripts/tests -p test_role_recovery.py -v
```

For an installation smoke check use fresh `-WorkerHome` and `-SkillRoot` paths containing spaces. Confirm
both launchers, all local runtime config values and the complete skill are present. A repeated install must
refuse overwrite without changing the first installation. Do not use real research data as test fixtures.
