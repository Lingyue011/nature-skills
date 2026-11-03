param([Parameter(Mandatory)][string]$JobFile,
      [string]$RunRoot=(Join-Path $PSScriptRoot 'runs'),
      [string]$Python='python',
      [string]$CliPath="$env:APPDATA/npm/node_modules/@opencode/cli/bin/opencode.exe")
$ErrorActionPreference='Stop'
$configPath=Join-Path $PSScriptRoot 'worker-config.json'
if(Test-Path -LiteralPath $configPath){
    $config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if(-not $PSBoundParameters.ContainsKey('Python')){$Python=$config.python}
    if(-not $PSBoundParameters.ContainsKey('CliPath')){$CliPath=$config.cli}
}
$mutex=[Threading.Mutex]::new($false,"Local\CodexDeepSeekPlotWorker-$env:USERNAME")
$held=$false; $code=2
try {
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException] {$held=$true}
    if(-not $held){$code=75; throw 'Another plotting job owns the new-worker lock.'}
    & $Python -X utf8 (Join-Path $PSScriptRoot 'plot_worker.py') --job $JobFile --run-root $RunRoot --pwsh (Get-Process -Id $PID).Path --cli $CliPath
    $code=$LASTEXITCODE
} catch {
    @{status='blocked_pending_root_review';error=$_.Exception.Message;exitCode=$code}|ConvertTo-Json -Compress
} finally {
    if($held){$mutex.ReleaseMutex()}; $mutex.Dispose()
}
exit $code
