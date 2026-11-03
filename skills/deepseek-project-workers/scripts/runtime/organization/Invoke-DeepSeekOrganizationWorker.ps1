param([Parameter(Mandatory)][ValidateSet('plan','dry-run','apply','rollback')][string]$Mode,
      [string]$JobFile,[string]$PlanFile,[string]$ApprovalFile,
      [string]$RunRoot=(Join-Path $PSScriptRoot 'runs'),[string]$Python='python',
      [string]$CliPath="$env:APPDATA/npm/node_modules/@opencode/cli/bin/opencode.exe")
$ErrorActionPreference='Stop'
$configPath=Join-Path $PSScriptRoot 'worker-config.json'
if(Test-Path -LiteralPath $configPath){
    $config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if(-not $PSBoundParameters.ContainsKey('Python')){$Python=$config.python}
    if(-not $PSBoundParameters.ContainsKey('CliPath')){$CliPath=$config.cli}
}
$mutex=[Threading.Mutex]::new($false,"Local\CodexDeepSeekOrganizationWorker-$env:USERNAME")
$held=$false;$code=2
try {
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException] {$held=$true}
    if(-not $held){$code=75;throw 'Organization worker busy'}
    $arguments=@('-B','-X','utf8',(Join-Path $PSScriptRoot 'organization_worker.py'),$Mode,'--run-root',$RunRoot,'--pwsh',(Get-Process -Id $PID).Path)
    $arguments+=@('--cli',$CliPath)
    if($JobFile){$arguments+=@('--job',$JobFile)}
    if($PlanFile){$arguments+=@('--plan',$PlanFile)}
    if($ApprovalFile){$arguments+=@('--approval',$ApprovalFile)}
    & $Python @arguments
    $code=$LASTEXITCODE
} catch {@{status='blocked_pending_root_review';error=$_.Exception.Message;exitCode=$code}|ConvertTo-Json -Compress}
finally {if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
exit $code
