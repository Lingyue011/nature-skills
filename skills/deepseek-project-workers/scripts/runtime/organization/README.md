# Installed organization worker

PowerShell modes: `plan -JobFile ...`, `dry-run/apply -PlanFile ... -ApprovalFile ...`,
or explicitly released `rollback -PlanFile ...`. Configuration is local `worker-config.json`,
with `-Python` and `-CliPath` overrides. See the companion skill's `references/setup-and-jobs.md` for fields.

Two or four logical review roles propose inventory IDs; Root reviews scientific dependencies and the exact plan.
Default transient replacement is two per failed role/four per job; completed roles and original budgets persist.
File moves are never automatically retried. The executor rejects overwrite, traversal and links, journals moves
under repository trash and never deletes. Empty/old files are not automatically obsolete.

Run results remain `pending_root_review`; a successful model review is not scientific acceptance.
