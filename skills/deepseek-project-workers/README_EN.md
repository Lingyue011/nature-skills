# DeepSeek Project Workers

[中文说明](README.md)

## Capabilities

Installable Windows OpenCode Go DS Flash MAX workers and a companion skill.
Drawing uses author A and independent visual reviewer B; organization uses two or up to four logical roles.
Upstream truncation replaces only the failed role while preserving completed results, evidence and budgets.
Root retains scientific definitions, source review and final acceptance.

## Installation

Requires PowerShell 7.2+, Python 3.12+, a native OpenCode CLI and a Go login performed on the target computer.

```powershell
python -m pip install -r .\skills\deepseek-project-workers\requirements.txt
pwsh -NoProfile -File .\skills\deepseek-project-workers\scripts\Install-Workers.ps1
```

Workers default to `$HOME/AgentTools`; the skill defaults to `$CODEX_HOME/skills` or `$HOME/.codex/skills`.
The installer discovers local Python/OpenCode paths and writes local configuration. It makes no model calls,
copies no credentials and refuses existing installations. Invoke `$deepseek-project-workers`.
See [setup and jobs](references/setup-and-jobs.md) for arguments and test commands.

## Boundaries and validation

Drawing executes only Root-reviewed renderers and layout schemas. Organization proposes inventory IDs;
an exact-list executor moves approved files into repository trash. There is no deletion, automatic move/solve retry,
scientific source editing or implicit Git push authorization. Defaults allow two replacements per role and four per job,
within the original wall/output budgets.

The originating workflow passed 22 offline tests, a real four-role organization pilot and a genuine MAX replacement
after an injected truncation. This distribution also has an isolated installation check using paths with spaces.
No research data, figures, sessions or account configuration are bundled. Windows only; installing this package
does not validate arbitrary scientific renderers or projects.
