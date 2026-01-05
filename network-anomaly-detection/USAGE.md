## Usage

### Local (Python environment)

```bash
cd network-anomaly-detection

# optional: create venv
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Run end-to-end smoke test
bash scripts/smoke_test.sh

# Or run components manually
python src/synthetic_data.py --rows 200 --output data/raw/sample.csv
python src/preprocess.py --input data/raw/sample.csv --output data/processed/processed.csv
python src/train_ml.py --data data/processed/processed.csv --out-model models/ml_best.pkl --mode quick
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
cd network-anomaly-detection
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d

# call API
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -G --data-urlencode "model=ml" --data-urlencode "path=models/ml_best.pkl" \
  --data '{"features": [1.0, 0.5, 3.2, 4.4, 5.5, 0.1, 2.2, 3.3, 4.4, 5.5]}'

# logs
docker compose -f docker/docker-compose.yml logs -f app
```

