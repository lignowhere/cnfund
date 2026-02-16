param(
    [string]$ServiceId = "",
    [switch]$SkipFinalRedeploy
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    if ($ServiceId) {
        Write-Host "Setting API_SEED_FORCE=true on service $ServiceId ..."
        railway variable set API_SEED_FORCE=true -s $ServiceId --skip-deploys

        Write-Host "Deploying backend with seed files ..."
        railway up --no-gitignore -s $ServiceId

        Write-Host "Setting API_SEED_FORCE=false ..."
        railway variable set API_SEED_FORCE=false -s $ServiceId --skip-deploys

        if (-not $SkipFinalRedeploy) {
            Write-Host "Redeploying once to lock normal mode ..."
            railway redeploy -s $ServiceId -y
        }
    } else {
        Write-Host "Setting API_SEED_FORCE=true ..."
        railway variable set API_SEED_FORCE=true --skip-deploys

        Write-Host "Deploying backend with seed files ..."
        railway up --no-gitignore

        Write-Host "Setting API_SEED_FORCE=false ..."
        railway variable set API_SEED_FORCE=false --skip-deploys

        if (-not $SkipFinalRedeploy) {
            Write-Host "Redeploying once to lock normal mode ..."
            railway redeploy -y
        }
    }

    Write-Host ""
    Write-Host "Seed workflow completed."
    Write-Host "Next check: open /health and then login to verify real data."
}
finally {
    Pop-Location
}
