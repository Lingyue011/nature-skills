# Root-owned native process boundary. No shell interpretation of model text.
param([Parameter(Mandatory)][string]$SpecFile)
$ErrorActionPreference='Stop'
$s=Get-Content -LiteralPath $SpecFile -Raw | ConvertFrom-Json
$p=$null; $o=$null; $e=$null; $reason=$null; $code=2
$watch=[Diagnostics.Stopwatch]::StartNew(); $started=$false
$stdinComplete=$false;$cleanupConfirmed=$false;$it=$null;$terminationRequested=$false
try {
    $psi=[Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$s.exe; $psi.WorkingDirectory=$s.cwd
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    if($s.inputFile){$psi.RedirectStandardInput=$true;$psi.StandardInputEncoding=[Text.UTF8Encoding]::new($false)}
    foreach($a in $s.arguments){[void]$psi.ArgumentList.Add([string]$a)}
    $p=[Diagnostics.Process]::new(); $p.StartInfo=$psi
    $o=[IO.File]::Create($s.stdout); $e=[IO.File]::Create($s.stderr)
    [void]$p.Start()
    $started=$true
    $pidOwned=$p.Id
    $ot=$p.StandardOutput.BaseStream.CopyToAsync($o)
    $et=$p.StandardError.BaseStream.CopyToAsync($e)
    $stdinComplete=-not [bool]$s.inputFile
    if($s.inputFile){
        $text=[IO.File]::ReadAllText($s.inputFile,[Text.Encoding]::UTF8)
        if($text.Length -gt 262144){throw 'stdin size limit'}
        $it=$p.StandardInput.WriteAsync($text)
    }
    while(-not $p.WaitForExit(200)) {
        if($it -and $it.IsCompleted){$it.GetAwaiter().GetResult();$p.StandardInput.Close();$it=$null;$stdinComplete=$true}
        if($watch.Elapsed.TotalSeconds -gt $s.timeout){$reason='timeout'; break}
        if(($o.Length+$e.Length) -gt $s.outputBytes){$reason='output_limit'; break}
    }
    if($reason){$terminationRequested=$true;$p.Kill($true);$cleanupConfirmed=$p.WaitForExit(10000)}
    else{$cleanupConfirmed=$p.HasExited}
    if($it){
        if(-not $it.IsCompleted){throw 'stdin write incomplete at process exit'}
        $it.GetAwaiter().GetResult();$p.StandardInput.Close();$it=$null;$stdinComplete=$true
    }
    [void][Threading.Tasks.Task]::WaitAll(@($ot,$et),10000)
    if(($o.Length+$e.Length) -gt $s.outputBytes){$reason='output_limit'}
    $code=if($reason){124}else{$p.ExitCode}
} catch { $reason=$_.Exception.Message } finally {
    if($p -and $started){
        try{
            if(-not $p.HasExited){$terminationRequested=$true;$p.Kill($true);$cleanupConfirmed=$p.WaitForExit(10000)}
            else{$cleanupConfirmed=$true}
        }catch{$cleanupConfirmed=$false}
    }
    if(-not $cleanupConfirmed){$reason='cleanup_unverified';$code=2}
    elseif($s.inputFile -and -not $stdinComplete){$reason='stdin_delivery_unverified';$code=2}
    if($o){$o.Dispose()}; if($e){$e.Dispose()}; if($p){$p.Dispose()}
    @{exitCode=$code;reason=$reason;pid=$pidOwned;seconds=$watch.Elapsed.TotalSeconds;
      stdinRequired=[bool]$s.inputFile;stdinComplete=$stdinComplete;cleanupConfirmed=$cleanupConfirmed;
      cleanupScope='direct-process-only';terminationRequested=$terminationRequested} |
        ConvertTo-Json -Compress | Set-Content -LiteralPath $s.receipt -Encoding utf8NoBOM
}
exit $code
