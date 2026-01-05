# Network Anomaly Detection Project

A machine learning project for detecting network anomalies and intrusions using various ML algorithms and deep learning techniques.

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Data
```bash
# Generate synthetic network flow data for testing
python src/synthetic_data.py --rows 100 --output data/raw/sample.csv
```

### 3. Run Analysis
```bash
# Start Jupyter notebook for data exploration
jupyter notebook notebooks/

# Or run specific scripts
python scripts/train_model.py
python scripts/evaluate_model.py
```

### 4. API Server (Optional)
```bash
# Start FastAPI server for model serving
uvicorn src.api:app --reload
```

## Project Structure

```
network-anomaly-detection/
├── data/
│   ├── raw/           # Raw data files
│   └── processed/     # Processed/cleaned data
├── notebooks/         # Jupyter notebooks for analysis
├── src/              # Source code
├── models/           # Trained model files
├── scripts/          # Utility scripts
├── reports/          # Analysis reports and visualizations
├── docker/           # Docker configuration
└── requirements.txt  # Python dependencies
```

## Features

- **Multiple ML Algorithms**: Random Forest, XGBoost, Neural Networks
- **Deep Learning**: TensorFlow/Keras models for complex patterns
- **API Interface**: FastAPI for model serving
- **Data Generation**: Synthetic data generation for testing
- **Visualization**: SHAP explanations and interactive plots
- **Imbalanced Learning**: Handle class imbalance in network data

## Usage Examples

```python
# Load and preprocess data
from src.data_loader import load_network_data
data = load_network_data('data/raw/sample.csv')

# Train anomaly detection model
from src.models import AnomalyDetector
detector = AnomalyDetector()
detector.train(data)

# Make predictions
predictions = detector.predict(new_data)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
