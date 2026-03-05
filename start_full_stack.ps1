# ============================================
# Full Stack Startup Script
# Starts Backend + Frontend + Checks Databases
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   KAPIVA FULL STACK STARTUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the project root directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# ============================================
# Step 1: Check Database Services
# ============================================
Write-Host "[1/4] Checking database services..." -ForegroundColor Yellow

# Check PostgreSQL (port 5432)
$postgresCheck = netstat -ano | Select-String ":5432.*LISTENING"
if (-not $postgresCheck) {
    Write-Host "  ⚠️  WARNING: PostgreSQL not detected on port 5432" -ForegroundColor Yellow
    Write-Host "     Make sure PostgreSQL service is running!" -ForegroundColor Yellow
    Write-Host "     You can start it with: Start-Service postgresql*" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ PostgreSQL is running (port 5432)" -ForegroundColor Green
}

# Check MongoDB (port 27017)
$mongoCheck = netstat -ano | Select-String ":27017.*LISTENING"
if (-not $mongoCheck) {
    Write-Host "  ⚠️  WARNING: MongoDB not detected on port 27017" -ForegroundColor Yellow
    Write-Host "     Make sure MongoDB service is running!" -ForegroundColor Yellow
    Write-Host "     You can start it with: Start-Service MongoDB*" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ MongoDB is running (port 27017)" -ForegroundColor Green
}

Write-Host ""

# ============================================
# Step 2: Check if Backend is already running
# ============================================
Write-Host "[2/4] Checking backend status..." -ForegroundColor Yellow

$backendCheck = netstat -ano | Select-String ":8000.*LISTENING"
if ($backendCheck) {
    Write-Host "  ⚠️  Backend is already running on port 8000" -ForegroundColor Yellow
    $stopBackend = Read-Host "  Do you want to stop it and restart? (Y/N)"
    if ($stopBackend -eq "Y" -or $stopBackend -eq "y") {
        Write-Host "  Stopping existing backend..." -ForegroundColor Yellow
        $pids = @()
        foreach ($line in $backendCheck) {
            $parts = $line -split '\s+'
            $pid = $parts[-1]
            if ($pid -and $pid -ne "0") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "    Process $pid stopped" -ForegroundColor Green
                } catch {
                    Write-Host "    Could not stop process $pid" -ForegroundColor Red
                }
            }
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "  Keeping existing backend running..." -ForegroundColor Green
        $skipBackend = $true
    }
} else {
    Write-Host "  ✅ Port 8000 is available" -ForegroundColor Green
    $skipBackend = $false
}

Write-Host ""

# ============================================
# Step 3: Start Backend
# ============================================
if (-not $skipBackend) {
    Write-Host "[3/4] Starting backend server..." -ForegroundColor Yellow
    Write-Host "  Backend will run on: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs will be at: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    
    # Set Python path
    $env:PYTHONPATH = "$projectRoot;$projectRoot\backend\app"
    
    # Start backend in a new window
    $backendScript = @"
cd `"$projectRoot\backend`"
`$env:PYTHONPATH = `"$projectRoot;$projectRoot\backend\app`"
Write-Host `"Starting backend on http://localhost:8000...`" -ForegroundColor Green
Write-Host `"Press CTRL+C to stop`" -ForegroundColor Yellow
Write-Host `"`"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
    Write-Host "  ✅ Backend starting in new window..." -ForegroundColor Green
    Write-Host "  Waiting 5 seconds for backend to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
} else {
    Write-Host "[3/4] Backend already running, skipping..." -ForegroundColor Green
}

Write-Host ""

# ============================================
# Step 4: Start Frontend
# ============================================
Write-Host "[4/4] Starting frontend..." -ForegroundColor Yellow

# Check if dist folder exists (production build)
$distPath = Join-Path $projectRoot "frontend\dist"
$frontendPort = 8080

if (Test-Path $distPath) {
    Write-Host "  📦 Production build found in frontend/dist" -ForegroundColor Cyan
    Write-Host "  Starting production server on port $frontendPort..." -ForegroundColor Cyan
    
    $frontendScript = @"
cd `"$distPath`"
Write-Host `"Starting frontend on http://localhost:$frontendPort...`" -ForegroundColor Green
Write-Host `"Press CTRL+C to stop`" -ForegroundColor Yellow
Write-Host `"`"
python -m http.server $frontendPort
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
    Write-Host "  ✅ Frontend starting in new window..." -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Production build not found. Checking for dev setup..." -ForegroundColor Yellow
    
    $packageJson = Join-Path $projectRoot "frontend\package.json"
    if (Test-Path $packageJson) {
        Write-Host "  📦 Starting Vue.js development server..." -ForegroundColor Cyan
        Write-Host "  Note: This may take a moment to compile..." -ForegroundColor Yellow
        
        $frontendScript = @"
cd `"$projectRoot\frontend`"
Write-Host `"Starting Vue.js dev server...`" -ForegroundColor Green
Write-Host `"This may take 30-60 seconds to compile...`" -ForegroundColor Yellow
Write-Host `"`"
npm run serve
"@
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
        Write-Host "  ✅ Frontend dev server starting in new window..." -ForegroundColor Green
        Write-Host "  ⏳ Please wait for compilation to complete..." -ForegroundColor Yellow
    } else {
        Write-Host "  ❌ Frontend not found! Please check frontend directory." -ForegroundColor Red
    }
}

Write-Host ""

# ============================================
# Summary
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   STARTUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access your application:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:$frontendPort" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Backend and Frontend are running in separate windows" -ForegroundColor Gray
Write-Host "   - Close those windows to stop the servers" -ForegroundColor Gray
Write-Host "   - Backend auto-reloads on code changes" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit this script (servers will keep running)..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
