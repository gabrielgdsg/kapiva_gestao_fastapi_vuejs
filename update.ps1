# Update Kapiva on Windows - run from project root
# Usage: .\update.ps1
#        .\update.ps1 -ComposeFile docker-compose.network-remote-with-mongo.yml

param(
    [string]$ComposeFile = "docker-compose.network-remote-with-mongo.yml"
)

Write-Host "Updating Kapiva (compose: $ComposeFile)..." -ForegroundColor Cyan

# Optional: pull latest from Git
if (Test-Path .git) {
    Write-Host "Pulling from Git..." -ForegroundColor Yellow
    git pull
}

Write-Host "Rebuilding and restarting containers..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d --build

Write-Host "Done. Access at http://localhost or http://192.168.1.170" -ForegroundColor Green
