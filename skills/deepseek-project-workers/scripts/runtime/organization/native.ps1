# Root-owned native process boundary. No shell interpretation of model text.
param([Parameter(Mandatory)][string]$SpecFile)
$ErrorActionPreference='Stop'
$s=Get-Content -LiteralPath $SpecFile -Raw | ConvertFrom-Json
$p=$null; $o=$null; $e=$null; $reason=$null; $code=2
$watch=[Diagnostics.Stopwatch]::StartNew(); $started=$false
try {
    $psi=[Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$s.exe; $psi.WorkingDirectory=$s.cwd
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    foreach($a in $s.arguments){[void]$psi.ArgumentList.Add([string]$a)}
    $p=[Diagnostics.Process]::new(); $p.StartInfo=$psi
    $o=[IO.File]::Create($s.stdout); $e=[IO.File]::Create($s.stderr)
    [void]$p.Start()
    $started=$true
    $pidOwned=$p.Id
    $ot=$p.StandardOutput.BaseStream.CopyToAsync($o)
    $et=$p.StandardError.BaseStream.CopyToAsync($e)
    while(-not $p.WaitForExit(200)) {
        if($watch.Elapsed.TotalSeconds -gt $s.timeout){$reason='timeout'; break}
        if(($o.Length+$e.Length) -gt $s.outputBytes){$reason='output_limit'; break}
    }
    if($reason){$p.Kill($true); [void]$p.WaitForExit(10000)}
    [void][Threading.Tasks.Task]::WaitAll(@($ot,$et),10000)
    if(($o.Length+$e.Length) -gt $s.outputBytes){$reason='output_limit'}
    $code=if($reason){124}else{$p.ExitCode}
} catch { $reason=$_.Exception.Message } finally {
    if($p -and $started -and -not $p.HasExited){$p.Kill($true); [void]$p.WaitForExit(10000)}
    if($o){$o.Dispose()}; if($e){$e.Dispose()}; if($p){$p.Dispose()}
    @{exitCode=$code;reason=$reason;pid=$pidOwned;seconds=$watch.Elapsed.TotalSeconds} |
        ConvertTo-Json -Compress | Set-Content -LiteralPath $s.receipt -Encoding utf8NoBOM
}
exit $code
