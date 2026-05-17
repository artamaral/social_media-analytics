param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [Parameter(Mandatory = $false)]
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
    $argsList = @("--dry-run", "--path", $Path, "--source-url", $SourceUrl)
    if ($ReferencePeriod) {
        $argsList += @("--reference-period", $ReferencePeriod)
    }

    py -3 $pythonScript @argsList
}
catch {
    python $pythonScript @argsList
}
