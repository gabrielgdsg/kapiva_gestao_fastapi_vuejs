#!/usr/bin/env bash
# Start the full dev stack (backend + frontend) with Docker. Run from project root.
# Backend and frontend auto-reload on code changes; backend also reloads on .env changes.
set -e
cd "$(dirname "$0")"

# Ensure backend .env exists so compose doesn't fail
if [ ! -f backend/.env ]; then
  if [ -f backend/.env.example ]; then
    echo "Creating backend/.env from .env.example (edit backend/.env with your keys)."
    cp backend/.env.example backend/.env
  else
    echo "Warning: backend/.env not found. Create it or copy from backend/.env.example."
  fi
fi

echo ""
echo "========================================"
echo "   Starting Kapiva dev stack"
echo "========================================"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:8080"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop everything."
echo "========================================"
echo ""

docker compose -f docker-compose.dev.yml up --build
