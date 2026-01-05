import json
from pathlib import Path

import pytest

from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def test_predict_endpoint_returns_expected_keys(client):
    # Arrange: minimal numeric features (length doesn't matter for validation here)
    sample_features = [1.0, 0.5, 3.2, 4.4, 5.5]

    # Act
    response = client.post(
        "/predict",
        params={"model": "ml", "path": "models/ml_best.pkl"},
        json={"features": sample_features},
    )

    # Assert HTTP
    assert response.status_code in (200, 404), (
        f"Unexpected status: {response.status_code}, body: {response.text}"
    )

    if response.status_code == 404:
        # Model file may be absent in CI; ensure proper error format
        body = response.json()
        assert "detail" in body
        return

    body = response.json()
    for key in ("label", "score", "model", "model_type"):
        assert key in body, f"Missing key in response: {key}"

