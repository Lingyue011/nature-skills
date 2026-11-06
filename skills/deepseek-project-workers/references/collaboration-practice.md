# DS drawing collaboration: reusable practice

Use this when preparing an author job, diagnosing latency, or assessing whether
the DS route is ready for a new figure type. It supplements AUTHOR_WORKFLOW.md;
it does not change scientific definitions or authorise publication.

## Prepare the contract

Root freezes inputs, units, reference state, metric definitions and scheme-label
meaning. Use a neutral shared figure goal. A writes presentation code, B reviews
the actual image and source, and Root controls execution release and acceptance.
Do not phrase the shared task as an instruction for B to write another program.

The input catalog contains names and byte counts, not file contents. With native
tools disabled, A can write a file reader from a sufficient schema but cannot be
assumed to have inspected the local CSV. Supply a Root-reviewed data_brief:

- filenames matching frozen inputs, columns, units and reference state;
- series labels, row/point counts, ranges and representative first/last rows;
- the exact meaning of included/excluded, on/off, nominal/effective or similar terms.

Small datasets may be included in full when useful and within approved budgets.
Full CSV inline is not mandatory and is unsuitable for large histories. Examples
are planning data, never substitute observations. The program reads all frozen
rows at execution. Worker code must not invent scientific statistics or silently
perform new filtering/calibration to prepare a brief; Root owns those operations.

Select the actual skill route: civil-curves for ordinary curves, civil-panels for
multi-panel charts, civil-paraview for FE rendering. Send all required selected
resources in full to both roles. Supply helper APIs or helper source when needed;
do not indiscriminately add unrelated resources. Skill delivery is not proof that
helpers executed or that the figure passed QA.

## Match actions to the stage

A returns a complete source program. It need not execute runtime or visual checks
before Root releases it, and must not claim those checks already passed. B sees
the actual image, source and machine QA; it gives concrete findings and a verified
image probe, not another author response. Root reviews each changed executable
source before execution and the final scientific meaning before adoption.

Read stage_summary.json rather than flattening all results into success/failure:
source received, exact release, execution/QA, image delivery, independent verdict,
and Root record are different outcomes. A reviewer timeout is not proof of failed
source authorship. A valid PNG or image probe is not scientific/physical validation.

## Wait cheaply and honestly

New drawing jobs default to 40 minutes per request and a finite three-hour whole
job budget; explicit short diagnostics remain possible. Root review pauses count
towards the whole-job budget. Heartbeats must not reset these deadlines.

Local scripts update observation files and record a silent heartbeat every ten
minutes. Do not repeatedly invoke Root just to narrate an unchanged wait. Reading
logs, source review and final acceptance still require Root work; do not promise
that the entire collaboration consumes zero main-model usage.

step_start, fresh local timestamps, CPU activity or debug-log growth do not prove
remote model progress. Missing visible output means progress unknown. Check
timestamp freshness and native receipts; stale pending is not liveness. The
watchdog enforces the authorised limit. Only verified owned timeout/transport
failures may replace that failed role inside the unchanged retry/wall budgets.
Keep completed roles, source, renders and failed attempts. No full-pipeline reset,
fallback model or automatic solve/render/move retry is implied.

## Diagnose with evidence

Use a small number of controlled tests: short response, representative complete
single-figure program, reviewed execution and independent actual-image review.
Do not repeatedly rerun successful stages or treat short echoes as coding proof.
Compare completed role receipts, visible output and reasoning token counts,
request duration and outcome. Zero usage on an unfinished request is inconclusive.

One accepted real time-history figure took about6.6min for A and8.6min for B,
with about71k and30k reasoning tokens. Both exceeded a former180s limit. This
supports longer limits for that task, not a claim that every earlier timeout was
overthinking or that40min is universally necessary. A successful synthetic case
does not prove every real-data or ParaView case works. Full-data visibility,
prompt length and QA burden were not independently established as sole causes.

## Preserve a reviewable delivery

Keep source and hash, exact execution approval, input/skill hashes, verified model
and session identities, machine QA, real-image review/probe and Root final record.
Root final acceptance binds source_sha256 and figure_sha256. State unresolved
stages explicitly. Do not rewrite historical frozen jobs during a worker upgrade.
Scientific figures and test/synthetic figures remain clearly identified.
