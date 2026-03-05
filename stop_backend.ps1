# Script para parar processos do backend
Write-Host "=== PARANDO PROCESSOS DO BACKEND ==="
Write-Host ""

# Encontrar processos usando a porta 8000
$port8000 = netstat -ano | Select-String ":8000.*LISTENING"
$pids = @()

if ($port8000) {
    foreach ($line in $port8000) {
        $parts = $line -split '\s+'
        $pid = $parts[-1]
        if ($pid -and $pid -ne "0") {
            $pids += $pid
        }
    }
}

if ($pids.Count -gt 0) {
    Write-Host "Processos encontrados na porta 8000:"
    foreach ($pid in $pids) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  PID: $pid - $($proc.ProcessName) (iniciado: $($proc.StartTime))"
        }
    }
    Write-Host ""
    $confirm = Read-Host "Deseja parar esses processos? (S/N)"
    if ($confirm -eq "S" -or $confirm -eq "s") {
        foreach ($pid in $pids) {
            try {
                Stop-Process -Id $pid -Force
                Write-Host "  Processo $pid parado com sucesso"
            } catch {
                Write-Host "  Erro ao parar processo $pid : $_"
            }
        }
        Write-Host ""
        Write-Host "Processos parados. Agora voce pode reiniciar o backend."
    } else {
        Write-Host "Operacao cancelada."
    }
} else {
    Write-Host "Nenhum processo encontrado na porta 8000."
}
