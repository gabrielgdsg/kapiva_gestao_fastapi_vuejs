# 🎉 Full Stack Running - Local Development Setup

**Date:** 2026-01-11  
**Status:** ✅ All systems operational

## 📊 System Overview

### **Databases (Native - No Docker!)**
Both databases running natively on Windows for **maximum performance** and **minimal resource usage**:

#### PostgreSQL 13.8
- **Host:** localhost:5432
- **Database:** LOGTEC (2.1 GB)
- **User:** postgres
- **Password:** postgres
- **Records:** 111,842 COMISSAO records
- **Installation:** Native Windows PostgreSQL service

#### MongoDB 8.2.3
- **Host:** localhost:27017
- **Connection:** mongodb://localhost:27017
- **Authentication:** None (local development)
- **Installation:** Chocolatey package (native Windows service)

### **Backend API**
- **URL:** http://localhost:80
- **Framework:** FastAPI + Uvicorn
- **Status:** ✅ Running with auto-reload
- **Connections:** 
  - ✅ PostgreSQL pool initialized
  - ✅ MongoDB initialized

### **Frontend**
- **URL:** http://localhost:8080
- **Framework:** Vue.js
- **Status:** ✅ Serving production build
- **Server:** Python HTTP server (stable)

## 🚀 How to Start Everything

### 1. Start Backend
```powershell
cd D:\PycharmProjects\kapiva_fixed
$env:PYTHONPATH="D:\PycharmProjects\kapiva_fixed;D:\PycharmProjects\kapiva_fixed\backend\app"
python -B -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 80
```

**Important:** Use `-B` flag to prevent bytecode caching issues!

### 2. Start Frontend
```powershell
cd D:\PycharmProjects\kapiva_fixed\frontend\dist
python -m http.server 8080
```

**Note:** Using production build for stability. Dev server has Node.js compatibility issues.

## ✅ Tested & Working Endpoints

### Vendas (Sales)
```
GET http://localhost:80/api/vendas/{cod_vendedor}/{date}
Example: http://localhost:80/api/vendas/1/2023-06-15
```

### Levantamentos (Product Inventory)
```
GET http://localhost:80/api/levantamentos/{data_ini}/{data_fim}/{cod_marca}
Example: http://localhost:80/api/levantamentos/2023-06-01/2023-06-30/1
✅ Tested: Returns 3077 lines of product data (97.7 KB)
```

### API Documentation
```
http://localhost:80/docs
```

## 📝 Configuration Files

### Environment File
**Location:** `D:\PycharmProjects\kapiva_fixed\develop_pycharm.env`

```env
# PostgreSQL (Local)
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DATABASE="LOGTEC"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

# MongoDB (Local)
MONGODB_URL="mongodb://localhost:27017"
```

## 🔧 Troubleshooting

### Backend won't connect to databases
1. Clear Python cache: `Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force`
2. Kill all Python processes: `Stop-Process -Name "python" -Force`
3. Restart backend with `-B` flag

### PostgreSQL not running
```powershell
# Check service
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Check port
netstat -ano | Select-String ":5432"
```

### MongoDB not running
```powershell
# Check port
netstat -ano | Select-String ":27017"

# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('Connected:', client.server_info()['version'])"
```

## 🎯 Access the Application

**Frontend:** http://localhost:8080  
**Backend API:** http://localhost:80  
**API Docs:** http://localhost:80/docs

## 💡 Benefits of This Setup

✅ **No Docker overhead** - Both databases run natively  
✅ **Faster performance** - Direct native execution  
✅ **Lower CPU/RAM usage** - No virtualization layer  
✅ **Easier debugging** - Direct access to all processes  
✅ **Auto-reload enabled** - Backend restarts on code changes  

## 📊 Resource Usage

Compared to Docker setup:
- **~500MB-1GB less RAM** (no Docker Desktop)
- **Lower CPU usage** (no virtualization)
- **Faster database queries** (no network translation)

---

**Setup completed:** 2026-01-11  
**All components tested and working!** 🎉
