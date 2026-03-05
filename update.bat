@echo off
REM Update Kapiva on Windows - run from project root
echo Updating Kapiva...

if exist .git (
    echo Pulling from Git...
    git pull
)

echo Rebuilding and restarting containers...
docker compose -f docker-compose.network.yml up -d --build

echo Done. Access at http://localhost or http://192.168.1.170
pause
