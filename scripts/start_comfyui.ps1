param(
    [string]$ComfyUIDir = "",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8188
)

if (-not $ComfyUIDir) {
    $ComfyUIDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "ComfyUI"
}

$ComfyUIDir = (Resolve-Path -LiteralPath $ComfyUIDir).Path
$Python = Join-Path $ComfyUIDir ".venv\Scripts\python.exe"
$Main = Join-Path $ComfyUIDir "main.py"
$Log = Join-Path $ComfyUIDir "comfyui.log"
$Err = Join-Path $ComfyUIDir "comfyui.err.log"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "ComfyUI Python not found: $Python"
}
if (-not (Test-Path -LiteralPath $Main)) {
    throw "ComfyUI main.py not found: $Main"
}

$existing = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*ComfyUI*" -and $_.CommandLine -like "*main.py*" } |
    Select-Object -First 1

if ($existing) {
    Write-Host "ComfyUI already appears to be running. PID: $($existing.ProcessId)"
    Write-Host "URL: http://$HostName`:$Port"
    exit 0
}

$process = Start-Process `
    -FilePath $Python `
    -ArgumentList @($Main, "--listen", $HostName, "--port", "$Port") `
    -WorkingDirectory $ComfyUIDir `
    -RedirectStandardOutput $Log `
    -RedirectStandardError $Err `
    -PassThru `
    -WindowStyle Hidden

Write-Host "Started ComfyUI. PID: $($process.Id)"
Write-Host "URL: http://$HostName`:$Port"
Write-Host "Log: $Err"
