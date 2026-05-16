param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [Parameter(Mandatory = $true)]
    [string]$ReferencePeriod,

    [Parameter(Mandatory = $true)]
    [string]$SourceUrl
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "ingest_fenabrave_phase1.py"

if (-not (Test-Path $pythonScript)) {
    throw "Script Python nao encontrado em: $pythonScript"
}

Set-Location $scriptDir

Write-Host "Iniciando extracao Fenabrave fase 1..."
Write-Host "Diretorio: $scriptDir"
Write-Host "Script: $pythonScript"

try {
    py -3 $pythonScript --dry-run --path $Path --reference-period $ReferencePeriod --source-url $SourceUrl
}
catch {
    python $pythonScript --dry-run --path $Path --reference-period $ReferencePeriod --source-url $SourceUrl
}
