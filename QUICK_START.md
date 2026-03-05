# 🚀 Quick Start Guide

## Option 1: One command (Docker, Linux/Mac)

From the project root:

```bash
./start-dev.sh
```

This starts backend + frontend with hot reload. No need to start each service separately.

- **Backend:** http://localhost:8000 (auto-restarts on code and `.env` changes)
- **Frontend:** http://localhost:8080 (Vue dev server with hot reload)
- **API docs:** http://localhost:8000/docs

Press `Ctrl+C` to stop everything. Requires Docker and Docker Compose.

---

## Option 2: Automated Startup (Windows, no Docker)

Run the startup script:

```powershell
.\start_full_stack.ps1
```

This script will:
- ✅ Check if databases are running
- ✅ Start backend on port 8000
- ✅ Start frontend on port 8080
- ✅ Open separate windows for each service

---

## Option 3: Manual Startup

### Start Backend

```powershell
cd backend
$env:PYTHONPATH="D:\PycharmProjects\kapiva_fixed;D:\PycharmProjects\kapiva_fixed\backend\app"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Or use the existing script:**
```powershell
.\start_backend.ps1
```

### Start Frontend

**Option A: Production Build (if dist folder exists)**
```powershell
cd frontend\dist
python -m http.server 8080
```

**Option B: Development Server**
```powershell
cd frontend
npm run serve
```

---

## Access URLs

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## Prerequisites

### Databases (Must be running)

1. **PostgreSQL** on port 5432
   - Check: `netstat -ano | Select-String ":5432"`
   - Start: `Start-Service postgresql*`

2. **MongoDB** on port 27017
   - Check: `netstat -ano | Select-String ":27017"`
   - Start: `Start-Service MongoDB*`

### Environment Variables

Make sure `develop_pycharm.env` exists in the project root with:
- PostgreSQL connection details
- MongoDB connection URL

---

## Troubleshooting

### Backend won't start
1. Check if port 8000 is in use: `netstat -ano | Select-String ":8000"`
2. Stop existing process: `.\stop_backend.ps1`
3. Clear Python cache: `Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force`

### Frontend won't start
1. If using dev server, make sure Node.js is installed
2. Install dependencies: `cd frontend && npm install`
3. If production build missing: `cd frontend && npm run build`

### Database connection errors
1. Verify PostgreSQL service is running
2. Verify MongoDB service is running
3. Check connection strings in `develop_pycharm.env`

---

## Stop Services

### Stop Backend
```powershell
.\stop_backend.ps1
```

### Stop Frontend
- Close the PowerShell window running the frontend
- Or find and kill the process: `Get-Process | Where-Object {$_.Path -like "*http.server*"}`

---

**Last Updated:** 2026-01-23
