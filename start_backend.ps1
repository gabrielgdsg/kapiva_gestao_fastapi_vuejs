# Script para iniciar o backend
Write-Host "=== INICIANDO BACKEND ==="
Write-Host ""

# Verificar se a porta 8000 está em uso
$port8000 = netstat -ano | Select-String ":8000.*LISTENING"
if ($port8000) {
    Write-Host "AVISO: Porta 8000 ja esta em uso!"
    Write-Host "Execute stop_backend.ps1 primeiro para parar os processos existentes."
    exit 1
}

# Mudar para o diretório backend
Set-Location backend

Write-Host "Iniciando backend na porta 8000..."
Write-Host "Pressione CTRL+C para parar"
Write-Host ""

# Iniciar uvicorn
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
