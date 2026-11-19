#!/usr/bin/env bash
# SaúdeFlow — projeto completo em modo standalone (macOS/Linux).
set -e
cd "$(dirname "$0")"

if [ ! -f frontend/dist/index.html ]; then
  echo "ERRO: frontend/dist não encontrado. Descompacte o zip inteiro antes de rodar."
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Baixando o uv (primeira vez, precisa de internet)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

cd backend
echo "[1/5] Criando ambiente Python..."
uv venv --python 3.11 .venv
echo "[2/5] Instalando dependências..."
uv pip install --python .venv/bin/python -r requirements.txt
echo "[3/5] Aplicando migrations..."
.venv/bin/python -m alembic upgrade head
echo "[4/5] Preparando dados de demonstração..."
.venv/bin/python -m app.seed
echo "[5/5] Iniciando em http://localhost:8000 ..."
( command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000 ) || open http://localhost:8000 || true
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
