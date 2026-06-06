$processes = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*ComfyUI*" -and $_.CommandLine -like "*main.py*" }

if (-not $processes) {
    Write-Host "No ComfyUI process found."
    exit 0
}

foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force
    Write-Host "Stopped ComfyUI PID: $($process.ProcessId)"
}
