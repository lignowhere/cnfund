param(
    [string]$ServiceId = "",
    [switch]$SkipFinalRedeploy,
    [switch]$SkipLocalUpload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    $setArgs = @(
        "variable",
        "set",
        "API_CNFUND_DATA_SOURCE=postgres",
        "API_POSTGRES_BOOTSTRAP_FROM_CSV=true",
        "--skip-deploys"
    )
    $redeployArgs = @("redeploy", "-y")
    $upArgs = @("up", "--no-gitignore")
    if ($ServiceId) {
        $setArgs += @("-s", $ServiceId)
        $redeployArgs += @("-s", $ServiceId)
        $upArgs += @("-s", $ServiceId)
    }

    Write-Host "Configuring service to bootstrap PostgreSQL from CSV..."
    & railway @setArgs

    if ($SkipLocalUpload) {
        Write-Host "SkipLocalUpload=true -> redeploying current source to run bootstrap..."
        & railway @redeployArgs
    } else {
        Write-Host "Uploading local source (with CSV files) and deploying for bootstrap..."
        & railway @upArgs
    }

    $resetArgs = @("variable", "set", "API_POSTGRES_BOOTSTRAP_FROM_CSV=false", "--skip-deploys")
    if ($ServiceId) {
        $resetArgs += @("-s", $ServiceId)
    }
    Write-Host "Disabling bootstrap flag after migration..."
    & railway @resetArgs

    if (-not $SkipFinalRedeploy) {
        Write-Host "Redeploying once more in normal mode..."
        & railway @redeployArgs
    }

    Write-Host ""
    Write-Host "PostgreSQL bootstrap workflow completed."
}
finally {
    Pop-Location
}
