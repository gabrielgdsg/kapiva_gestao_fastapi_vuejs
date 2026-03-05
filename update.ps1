# Update Kapiva on Windows - run from project root
# Usage: .\update.ps1

Write-Host "Updating Kapiva..." -ForegroundColor Cyan

# Optional: pull latest from Git
if (Test-Path .git) {
    Write-Host "Pulling from Git..." -ForegroundColor Yellow
    git pull
}

Write-Host "Rebuilding and restarting containers..." -ForegroundColor Yellow
docker compose -f docker-compose.network.yml up -d --build

Write-Host "Done. Access at http://localhost or http://192.168.1.170" -ForegroundColor Green
