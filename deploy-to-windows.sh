#!/usr/bin/env bash
# Deploy Kapiva to Windows server (192.168.1.170) - run from project root
# Uses tar+scp. Requires SSH key auth.
#
# Backend uses a volume mount (./backend:/app), so deploys are fast:
# sync files → clear pycache → restart container. No image rebuild needed.
#
# MongoDB data is in a named Docker volume (mongo_data) and is never
# affected by deploys. Your data is safe across all restarts and resyncs.
#
# Usage:
#   ./deploy-to-windows.sh                # sync + restart backend
#   ./deploy-to-windows.sh --full-rebuild # rebuild images (use after compose/Dockerfile changes)
#   ./deploy-to-windows.sh --sync-only    # sync files only, no restart
#   ./deploy-to-windows.sh --verify       # check what's on Windows without deploying

set -e

HOST="gabriel@192.168.1.170"
REMOTE_DIR="C:/kapiva_fixed"
COMPOSE_FILE="docker-compose.network-remote-with-mongo.yml"
TARBALL="kapiva_deploy.tar.gz"
SYNC_ONLY=false
FULL_REBUILD=false
VERIFY=false

for arg in "$@"; do
  [[ "$arg" == "--sync-only" ]]    && SYNC_ONLY=true
  [[ "$arg" == "--full-rebuild" ]] && FULL_REBUILD=true
  [[ "$arg" == "--verify" ]]       && VERIFY=true
done

cleanup() { rm -f "/tmp/$TARBALL"; }
trap cleanup EXIT

# helper: run a single powershell command over SSH
psh() { ssh "$HOST" "powershell -NoProfile -Command \"$*\""; }

# ── Verify mode ───────────────────────────────────────────────────────────────
if [ "$VERIFY" = true ]; then
  echo "=== Checking Windows file structure ==="
  echo "--- C:\\kapiva_fixed top level ---"
  psh "Get-ChildItem 'C:\\kapiva_fixed\\' | Select-Object Name, LastWriteTime"
  echo ""
  echo "--- backend/app/api/levantamentos ---"
  psh "if (Test-Path 'C:\\kapiva_fixed\\backend\\app\\api\\levantamentos\\') { Get-ChildItem 'C:\\kapiva_fixed\\backend\\app\\api\\levantamentos\\' | Select-Object Name, LastWriteTime } else { Write-Host 'PATH NOT FOUND' }"
  echo ""
  echo "--- Volume mounts on kapiva-backend ---"
  psh "docker inspect kapiva-backend --format '{{json .Mounts}}'"
  echo ""
  echo "--- Key method in container ---"
  psh "docker exec kapiva-backend grep -n 'load_marcas_fornecedores_from_db' /app/app/api/levantamentos/levantamentos_postgres.py"
  exit 0
fi

# ── 1. Clear local pycache before archiving ───────────────────────────────────
echo "Clearing local __pycache__..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# ── 2. Create archive ─────────────────────────────────────────────────────────
# Cache-bust frontend: touch file so Docker COPY layer is invalidated
echo "$(date +%s)" > frontend/.cachebust
echo "Creating archive..."
tar czf "/tmp/$TARBALL" \
  --exclude=node_modules --exclude=__pycache__ --exclude=.venv --exclude=.git \
  --exclude=frontend/dist --exclude=backend/logs --exclude="*.pyc" \
  --exclude=db_mongo/data \
  -C . .

echo "Archive size: $(du -sh /tmp/$TARBALL | cut -f1)"
echo "Checking archive contains levantamentos_postgres.py..."
tar tzf "/tmp/$TARBALL" | grep levantamentos_postgres || echo "WARNING: not found in archive!"

# ── 3. Transfer tarball ───────────────────────────────────────────────────────
echo ""
echo "Deploying to $HOST..."
psh "New-Item -ItemType Directory -Path 'C:\\kapiva_fixed' -Force | Out-Null"
scp "/tmp/$TARBALL" "$HOST:C:/kapiva_fixed/$TARBALL"
echo "Upload complete."

# ── 4. Extract ────────────────────────────────────────────────────────────────
echo "Extracting on Windows..."
psh "tar xzf 'C:\\kapiva_fixed\\$TARBALL' -C 'C:\\kapiva_fixed\\'; Write-Host 'tar exit:' \$LASTEXITCODE"
psh "Remove-Item 'C:\\kapiva_fixed\\$TARBALL' -Force; Write-Host 'tarball removed'"

# ── 5. Verify sync ────────────────────────────────────────────────────────────
echo "Verifying sync..."
psh "if (Test-Path 'C:\\kapiva_fixed\\backend\\app\\api\\levantamentos\\levantamentos_postgres.py') { Write-Host 'OK: file exists' } else { Write-Host 'ERROR: file missing after extract!' }"
psh "\$m = Select-String -Path 'C:\\kapiva_fixed\\backend\\app\\api\\levantamentos\\levantamentos_postgres.py' -Pattern 'load_marcas_fornecedores_from_db' -SimpleMatch; if (\$m) { Write-Host 'OK: method found in synced file' } else { Write-Host 'WARN: method missing in synced file!' }"

# ── 6. Clear pycache on Windows ───────────────────────────────────────────────
echo "Clearing __pycache__ on Windows..."
psh "Get-ChildItem 'C:\\kapiva_fixed\\backend' -Recurse -Filter '__pycache__' -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force; Write-Host 'pycache cleared'"

echo "Files synced to $REMOTE_DIR"

# ── 7. Docker step ────────────────────────────────────────────────────────────
if [ "$SYNC_ONLY" = true ]; then
  echo ""
  echo "Sync only — skipping container restart."
  echo "On Windows run: cd C:\\kapiva_fixed && docker compose -f $COMPOSE_FILE restart backend"

elif [ "$FULL_REBUILD" = true ]; then
  # Use this when you change Dockerfile, requirements.txt, or docker-compose.yml
  echo "Full rebuild: stopping containers, rebuilding images, starting fresh..."
  psh "\$env:DOCKER_CONFIG = 'C:\\Users\\gabriel\\.docker'; Set-Location 'C:\\kapiva_fixed'; docker compose -f $COMPOSE_FILE down --rmi local; Write-Host 'containers down'"
  psh "\$env:DOCKER_CONFIG = 'C:\\Users\\gabriel\\.docker'; Set-Location 'C:\\kapiva_fixed'; docker compose -f $COMPOSE_FILE build --no-cache --pull; Write-Host 'build complete'"
  psh "\$env:DOCKER_CONFIG = 'C:\\Users\\gabriel\\.docker'; Set-Location 'C:\\kapiva_fixed'; docker compose -f $COMPOSE_FILE up -d; Write-Host 'containers up'"
  echo ""
  echo "Full rebuild complete! Access at http://192.168.1.170"

else
  # Normal deploy: volume mount means we just need to restart the container
  echo "Restarting backend container..."
  psh "\$env:DOCKER_CONFIG = 'C:\\Users\\gabriel\\.docker'; Set-Location 'C:\\kapiva_fixed'; docker compose -f $COMPOSE_FILE restart backend; Write-Host 'Backend restarted.'"
  echo ""
  echo "Deploy complete! Access at http://192.168.1.170"
  echo ""
  echo "Verify with:"
  echo "  curl -s http://192.168.1.170:8000/api/reloadfrompostgresdb/marcafornecedor/"
fi