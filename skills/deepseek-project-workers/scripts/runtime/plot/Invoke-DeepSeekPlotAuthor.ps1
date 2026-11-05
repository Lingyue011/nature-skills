param([Parameter(Mandatory)][ValidateSet('start','resume')][string]$Mode,
      [string]$JobFile,[string]$Run,[string]$ApprovalFile,
      [string]$RunRoot=(Join-Path $PSScriptRoot 'author_runs'))
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'worker-config.json') -Raw|ConvertFrom-Json
$arguments=@('-B','-X','utf8',(Join-Path $PSScriptRoot 'author_worker.py'),$Mode,'--pwsh',$config.pwsh,'--cli',$config.cli,'--run-root',$RunRoot)
if($JobFile){$arguments+=@('--job',$JobFile)}
if($Run){$arguments+=@('--run',$Run)}
if($ApprovalFile){$arguments+=@('--approval',$ApprovalFile)}
& $config.python @arguments
exit $LASTEXITCODE
