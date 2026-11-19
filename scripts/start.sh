# Sobe o SaúdeFlow localmente (sem Docker)
# Uso: bash scripts/start.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Backend =="
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  uv venv --python 3.11 .venv
  uv pip install --python .venv/Scripts/python.exe -r requirements.txt 2>/dev/null || \
  uv pip install --python .venv/bin/python -r requirements.txt
fi
PYTHON_BIN=".venv/Scripts/python.exe"; [ -f "$PYTHON_BIN" ] || PYTHON_BIN=".venv/bin/python"
$PYTHON_BIN -m app.seed
$PYTHON_BIN -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!

echo "== Frontend =="
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install --no-audit --no-fund; fi
npm run dev &
FRONT_PID=$!

trap "kill $BACK_PID $FRONT_PID 2>/dev/null || true" EXIT
echo "Backend: http://localhost:8000/docs  |  Frontend: http://localhost:5173"
wait
