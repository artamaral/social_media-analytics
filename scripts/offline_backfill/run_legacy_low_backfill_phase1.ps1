$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "legacy_low_backfill_phase1.py"
$logsDir = Join-Path $scriptDir "logs"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$runLog = Join-Path $logsDir "legacy_low_backfill_phase1_$timestamp.log"
$latestLog = Join-Path $logsDir "legacy_low_backfill_phase1_latest.log"

if (-not (Test-Path $pythonScript)) {
    throw "Script Python nao encontrado em: $pythonScript"
}

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

Set-Location $scriptDir
$env:PYTHONIOENCODING = "utf-8"

$pythonCommand = $null

foreach ($candidate in @("py", "python")) {
    $resolved = Get-Command $candidate -ErrorAction SilentlyContinue

    if ($resolved) {
        $pythonCommand = $resolved.Source
        break
    }
}

if (-not $pythonCommand) {
    throw "Nenhum interpretador Python encontrado via 'py' ou 'python'."
}

$banner = @(
    "Iniciando backfill offline legacy_low fase 1..."
    "Diretorio: $scriptDir"
    "Script: $pythonScript"
    "Python: $pythonCommand"
    "Log da execucao: $runLog"
)

$banner | Tee-Object -FilePath $runLog

$exitCode = $null

try {
    if ((Split-Path $pythonCommand -Leaf).ToLower() -eq "py.exe" -or
        (Split-Path $pythonCommand -Leaf).ToLower() -eq "py") {
        & $pythonCommand -3 $pythonScript 2>&1 | Tee-Object -FilePath $runLog -Append
    }
    else {
        & $pythonCommand $pythonScript 2>&1 | Tee-Object -FilePath $runLog -Append
    }

    $exitCode = $LASTEXITCODE
}
finally {
    if ($null -eq $exitCode) {
        $exitCode = $LASTEXITCODE
    }

    @(
        "Codigo de saida: $exitCode"
        "Fim da execucao: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
    ) | Tee-Object -FilePath $runLog -Append

    Copy-Item -LiteralPath $runLog -Destination $latestLog -Force
}

if ($exitCode -ne 0) {
    throw "Backfill finalizado com codigo de saida $exitCode. Verifique: $latestLog"
}
