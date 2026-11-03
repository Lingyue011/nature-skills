#requires -Version 7.2
[CmdletBinding()]
param(
    [string]$WorkerHome=$env:DEEPSEEK_WORKER_HOME,
    [string]$SkillRoot,
    [string]$PythonPath,
    [string]$CliPath,
    [switch]$SkipSkill,
    [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
if(-not $IsWindows){throw 'This runtime currently supports Windows only.'}
$profilePath=[Environment]::GetFolderPath('UserProfile')
if(-not $WorkerHome){$WorkerHome=Join-Path $profilePath 'AgentTools'}
if(-not $SkillRoot){
    $codexRoot=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $profilePath '.codex'}
    $SkillRoot=Join-Path $codexRoot 'skills'
}
if(-not $PythonPath){$PythonPath=(Get-Command python.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source}
if(-not $CliPath){
    $candidate=Join-Path $env:APPDATA 'npm/node_modules/@opencode/cli/bin/opencode.exe'
    if(Test-Path -LiteralPath $candidate -PathType Leaf){$CliPath=$candidate}
    else{$CliPath=(Get-Command opencode.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source}
}
$PythonPath=(Get-Item -LiteralPath $PythonPath).FullName
$CliPath=(Get-Item -LiteralPath $CliPath).FullName
if([IO.Path]::GetExtension($CliPath) -ne '.exe'){throw 'CliPath must point to the native opencode.exe, not a cmd/ps1 shim.'}
$probe=& $PythonPath -B -X utf8 -c 'import json,sys,importlib.util; print(json.dumps({"version":list(sys.version_info[:3]),"python":sys.executable,"missing":[m for m in ["matplotlib","numpy","PIL"] if importlib.util.find_spec(m) is None]}))'
if($LASTEXITCODE -ne 0){throw 'Python dependency probe failed.'}
$runtime=$probe|ConvertFrom-Json
if($runtime.version[0] -ne 3 -or $runtime.version[1] -lt 12){throw 'Python 3.12+ is required.'}
if($runtime.missing.Count){throw ('Install requirements.txt first. Missing: '+($runtime.missing -join ', '))}
$PythonPath=$runtime.python
$sourceSkill=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '..')).FullName
$WorkerHome=[IO.Path]::GetFullPath($WorkerHome)
$SkillRoot=[IO.Path]::GetFullPath($SkillRoot)
$destinationSkill=Join-Path $SkillRoot 'deepseek-project-workers'
$targets=@(
    @{source=(Join-Path $PSScriptRoot 'runtime/plot');destination=(Join-Path $WorkerHome 'DeepSeekPlotWorker')},
    @{source=(Join-Path $PSScriptRoot 'runtime/organization');destination=(Join-Path $WorkerHome 'DeepSeekOrganizationWorker')}
)
foreach($target in $targets){if(Test-Path -LiteralPath $target.destination){throw ('Refusing to overwrite existing worker: '+$target.destination)}}
$copySkill=-not $SkipSkill -and $sourceSkill -ne $destinationSkill
if($copySkill -and (Test-Path -LiteralPath $destinationSkill)){throw 'Skill destination exists. Use its own installer or select -SkipSkill/-SkillRoot; no automatic replacement.'}
# Check complete destinations before any writes, including links in existing parents.
foreach($path in @($WorkerHome,$SkillRoot)){
    $node=[IO.DirectoryInfo]::new($path)
    while($node){
        if($node.Exists -and ($node.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked installation paths are not supported.'}
        $node=$node.Parent
    }
}
if($CheckOnly){
    @{status='preflight_passed';workerHome=$WorkerHome;skillRoot=$SkillRoot;python=$PythonPath;cli=$CliPath}|ConvertTo-Json -Compress
    exit 0
}
function Copy-PackageFiles([string]$Source,[string]$Destination){
    [void][IO.Directory]::CreateDirectory($Destination)
    foreach($file in Get-ChildItem -LiteralPath $Source -File -Recurse){
        $relative=[IO.Path]::GetRelativePath($Source,$file.FullName)
        if($relative -match '(^|[\\/])(__pycache__|runs)([\\/]|$)' -or $file.Name -eq 'worker-config.json' -or $file.Extension -eq '.pyc'){continue}
        if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Package contains a linked file.'}
        $dest=Join-Path $Destination $relative
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dest))
        Copy-Item -LiteralPath $file.FullName -Destination $dest -ErrorAction Stop
    }
}
foreach($target in $targets){
    Copy-PackageFiles $target.source $target.destination
    @{schema_version=1;python=$PythonPath;cli=$CliPath;pwsh=(Get-Process -Id $PID).Path}|
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $target.destination 'worker-config.json') -Encoding utf8NoBOM
}
if($copySkill){Copy-PackageFiles $sourceSkill $destinationSkill}
@{status='installed';workerHome=$WorkerHome;skill=if($SkipSkill){$null}else{$destinationSkill};
  entries=@($targets|ForEach-Object {$_.destination});model='opencode-go/deepseek-v4.1-flash#max';
  modelCalls=0;globalConfigurationChanged=$false}|ConvertTo-Json -Depth 4 -Compress
