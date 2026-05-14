$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "legacy_low_backfill_phase1.py"

if (-not (Test-Path $pythonScript)) {
    throw "Script Python nao encontrado em: $pythonScript"
}

Set-Location $scriptDir

Write-Host "Iniciando backfill offline legacy_low fase 1..."
Write-Host "Diretorio: $scriptDir"
Write-Host "Script: $pythonScript"

try {
    py -3 $pythonScript
}
catch {
    python $pythonScript
}
