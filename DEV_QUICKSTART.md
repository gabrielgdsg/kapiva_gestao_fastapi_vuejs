# Development (no rebuild on code change)

## Option 1: No Docker (fastest)

From project root:

```bash
./start-dev.sh
# or
make dev
```

- **Backend** http://localhost:8000 (reloads on file change)
- **Frontend** http://localhost:8080 (hot reload)
- Stop with **Ctrl+C** (stops both)

Requires: Python 3.10+, Node 18+, and MongoDB (local or set in `develop_pycharm.env` at project root).

## Option 2: Docker with hot reload

First time (build images):

```bash
make dev-docker-build
# or
docker compose -f docker-compose.dev.yml up --build
```

Later (no rebuild):

```bash
make dev-docker
# or
docker compose -f docker-compose.dev.yml up
```

- **Frontend** http://localhost:8080 (proxy to backend)
- **Backend** http://localhost:8000
- Code changes in `backend/` and `frontend/` are reflected without rebuilding.

Stop with **Ctrl+C**.

### Restarting the Docker dev server

If a route fails to load (e.g. ChunkLoadError) or the app feels stale, restart the stack:

```bash
# From project root
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up --build
```

Or in one line: `docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up --build`

Use `--build` so the frontend image is rebuilt with the latest code. Then open http://localhost:8080/pedidos-chegando
