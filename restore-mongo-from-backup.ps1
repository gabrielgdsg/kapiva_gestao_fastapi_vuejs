# Restore MongoDB from backup (run on Windows, in PowerShell as Admin)
# Backup location: C:\mongo_backup\kapiva_gestao
# Requires: kapiva-mongo container running (docker compose up -d)

$BackupPath = "C:\mongo_backup"
$NetworkName = "kapiva_fixed_default"  # from docker-compose project name

Write-Host "Restoring MongoDB from $BackupPath..."
Write-Host ""

# Check backup exists
if (-not (Test-Path "$BackupPath\kapiva_gestao")) {
    Write-Host "ERROR: Backup folder not found at $BackupPath\kapiva_gestao"
    exit 1
}

# Check mongo is running
$mongo = docker ps --filter "name=kapiva-mongo" --format "{{.Names}}"
if (-not $mongo) {
    Write-Host "ERROR: kapiva-mongo container not running. Start with: docker compose -f docker-compose.network-remote-with-mongo.yml up -d"
    exit 1
}

Write-Host "Using mongo container: $mongo"
Write-Host ""

# Run mongorestore in a temporary container, connected to the same network
# Mount backup dir and restore to mongo:27017
docker run --rm `
  -v "${BackupPath}:/backup:ro" `
  --network $NetworkName `
  mongo:8 `
  mongorestore --host mongo --port 27017 /backup

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Restore complete! Restart backend to pick up data:"
    Write-Host "  docker compose -f docker-compose.network-remote-with-mongo.yml restart backend"
} else {
    Write-Host ""
    Write-Host "Restore failed. Check the error above."
    exit 1
}
