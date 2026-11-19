# Sobe o SaúdeFlow localmente (sem Docker) — Windows PowerShell
# Uso: powershell -ExecutionPolicy Bypass -File scripts/start.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

Write-Host "== Backend ==" -ForegroundColor Cyan
Set-Location "$root\backend"
if (-not (Test-Path .venv)) {
  uv venv --python 3.11 .venv
  uv pip install --python .venv\Scripts\python.exe -r requirements.txt
}
.venv\Scripts\python.exe -m app.seed
$backend = Start-Process -FilePath ".venv\Scripts\python.exe" `
  -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -PassThru

Write-Host "== Frontend ==" -ForegroundColor Cyan
Set-Location "$root\frontend"
if (-not (Test-Path node_modules)) { npm install --no-audit --no-fund }
$frontend = Start-Process -FilePath "npm" -ArgumentList "run","dev" -PassThru

Write-Host "Backend: http://localhost:8000/docs  |  Frontend: http://localhost:5173"
Write-Host "Pressione Ctrl+C para encerrar."
try { Wait-Process -Id $backend.Id, $frontend.Id }
finally { Stop-Process -Id $backend.Id, $frontend.Id -ErrorAction SilentlyContinue }
