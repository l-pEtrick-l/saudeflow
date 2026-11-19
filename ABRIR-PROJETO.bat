@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo   SaudeFlow - PROJETO COMPLETO (modo 1 clique)
echo ==================================================
echo.

if not exist "frontend\dist\index.html" (
  echo ERRO: a pasta frontend\dist nao foi encontrada.
  echo Descompacte o zip inteiro antes de rodar.
  pause
  exit /b 1
)

REM --- localiza o uv (gerenciador rapido de Python) ---
set "UV="
if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
if not defined UV if exist "%CD%\.uv\uv.exe" set "UV=%CD%\.uv\uv.exe"

if not defined UV (
  echo Baixando o uv (primeira vez, precisa de internet)...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
  if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
)

if not defined UV (
  echo Nao foi possivel obter o uv. Instale em https://astral.sh e tente de novo.
  pause
  exit /b 1
)

echo Usando uv: %UV%
echo.

cd backend

echo [1/5] Criando ambiente Python...
"%UV%" venv --python 3.11 .venv

echo [2/5] Instalando dependencias (primeira vez, precisa de internet)...
"%UV%" pip install --python .venv\Scripts\python.exe -r requirements.txt

echo [3/5] Aplicando migrations...
.venv\Scripts\python.exe -m alembic upgrade head

echo [4/5] Preparando dados de demonstracao...
.venv\Scripts\python.exe -m app.seed

echo [5/5] Iniciando o sistema em http://localhost:8000 ...
start "" http://localhost:8000

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
