param(
    [switch]$InstallDeps,
    [int]$FrontendPort = 3000,
    [int]$BackendPort = 8001,
    [string]$BackendHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend_app"
$backendRoot = Join-Path $repoRoot "backend_api"
$frontendEnvExample = Join-Path $frontendRoot ".env.example"
$frontendEnvLocal = Join-Path $frontendRoot ".env.local"
$pythonVenv = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $pythonVenv) {
    $pythonExe = $pythonVenv
} else {
    $pythonExe = "python"
}

if (-not (Test-Path $frontendEnvLocal) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnvLocal
    Write-Host "Created frontend_app/.env.local from .env.example"
}

if ($InstallDeps) {
    Write-Host "Installing backend dependencies..."
    & $pythonExe -m pip install -r "$backendRoot\requirements.txt"

    Write-Host "Installing frontend dependencies..."
    Push-Location $frontendRoot
    npm install
    Pop-Location
}

$apiBaseUrl = "http://$BackendHost`:$BackendPort/api/v1"
$backendCommand = "Set-Location '$repoRoot'; & '$pythonExe' -m uvicorn backend_api.app.main:app --reload --host $BackendHost --port $BackendPort"
$frontendCommand = "Set-Location '$frontendRoot'; `$env:NEXT_PUBLIC_API_BASE_URL='$apiBaseUrl'; `$env:PORT='$FrontendPort'; npm run dev"

Write-Host "Starting backend API on http://$BackendHost`:$BackendPort ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    $backendCommand
)

Start-Sleep -Seconds 2

Write-Host "Starting frontend on http://localhost:$FrontendPort ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    $frontendCommand
)

Write-Host ""
Write-Host "Stack launched."
Write-Host "Frontend: http://localhost:$FrontendPort/login"
Write-Host "Backend docs: http://$BackendHost`:$BackendPort/docs"
Write-Host "API base: $apiBaseUrl"
