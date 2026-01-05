#!/usr/bin/env bash

set -euo pipefail

# Navigate to repository root (directory containing this script is network-anomaly-detection/scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "[INFO] Repo root: $REPO_ROOT"

# Optional: create and use a virtual environment if not already active
if [[ -z "${VIRTUAL_ENV-}" ]];
then
  echo "[INFO] Creating virtual environment .venv (optional)"
  python -m venv .venv
  source .venv/bin/activate
fi

echo "[INFO] Installing requirements"
pip install --upgrade pip
pip install -r requirements.txt

echo "[STEP] Generate synthetic data"
python src/synthetic_data.py --rows 200 --output data/raw/sample.csv

echo "[STEP] Run preprocessing pipeline"
python src/preprocess.py --input data/raw/sample.csv --output data/processed/processed.csv

echo "[STEP] Train quick ML model"
python src/train_ml.py --data data/processed/processed.csv --out-model models/ml_best.pkl --mode quick

echo "[STEP] Start API server (background)"
uvicorn src.api:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
echo "[INFO] uvicorn PID: $UVICORN_PID"

cleanup() {
  echo "[CLEANUP] Stopping uvicorn (PID $UVICORN_PID)"
  kill $UVICORN_PID 2>/dev/null || true
}
trap cleanup EXIT

echo "[INFO] Waiting for API to become ready..."
for i in {1..30}; do
  if curl -fsS http://localhost:8000/health >/dev/null; then
    echo "[INFO] API is ready"
    break
  fi
  sleep 1
done

echo "[STEP] Call /predict"
curl -sS -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -G --data-urlencode "model=ml" --data-urlencode "path=models/ml_best.pkl" \
  --data '{"features": [1.0, 0.5, 3.2, 4.4, 5.5, 0.1, 2.2, 3.3, 4.4, 5.5]}' | jq '.' || true

echo "[DONE] Smoke test complete"

