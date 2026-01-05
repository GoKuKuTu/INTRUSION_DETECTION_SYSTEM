import os
from pathlib import Path
from sklearn.dummy import DummyClassifier
import joblib
import numpy as np

models_dir = Path(__file__).parent.parent / 'models'
models_dir.mkdir(parents=True, exist_ok=True)

# Create a trivial classifier that always predicts 0 (normal)
X = np.array([[0],[1]])
y = np.array([0,0])
clf = DummyClassifier(strategy='most_frequent')
clf.fit(X,y)

model_path = models_dir / 'ml_best.pkl'
joblib.dump(clf, model_path)
print(f'Wrote dummy model to: {model_path}')
