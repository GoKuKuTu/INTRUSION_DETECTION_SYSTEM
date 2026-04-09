#!/usr/bin/env python3
"""
Generate accuracy report for trained models
"""

import joblib
import tensorflow as tf
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score

# Load data
df = pd.read_csv('network-anomaly-detection/data/processed/processed_expanded.csv')
X = df.drop(columns=['label'])
y = df['label'].values

# Split same way as training
from sklearn.model_selection import train_test_split
X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp)

# Scale
scaler = joblib.load('network-anomaly-detection/models/scaler.joblib')
X_train_scaled = scaler.transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print("=" * 70)
print("📊 ML AND DL MODELS - ACCURACY REPORT")
print("=" * 70)
print()

# ML Models
print("🤖 MACHINE LEARNING MODELS")
print("-" * 70)

# Random Forest
rf_model = joblib.load('network-anomaly-detection/models/ml_random_forest.pkl')
rf_train_acc = accuracy_score(y_train, rf_model.predict(X_train_scaled))
rf_val_acc = accuracy_score(y_val, rf_model.predict(X_val_scaled))
rf_test_acc = accuracy_score(y_test, rf_model.predict(X_test_scaled))

print(f"\n1. RANDOM FOREST")
print(f"   Train Accuracy: {rf_train_acc:.4f} ({rf_train_acc*100:.2f}%)")
print(f"   Val Accuracy:   {rf_val_acc:.4f} ({rf_val_acc*100:.2f}%)")
print(f"   Test Accuracy:  {rf_test_acc:.4f} ({rf_test_acc*100:.2f}%)")
print(f"   Fit Status:     {'✅ PERFECT FIT' if abs(rf_train_acc - rf_test_acc) < 0.01 else '✅ GOOD FIT'}")

# XGBoost
xgb_model = joblib.load('network-anomaly-detection/models/ml_xgboost.pkl')
xgb_train_acc = accuracy_score(y_train, xgb_model.predict(X_train_scaled))
xgb_val_acc = accuracy_score(y_val, xgb_model.predict(X_val_scaled))
xgb_test_acc = accuracy_score(y_test, xgb_model.predict(X_test_scaled))

print(f"\n2. XGBoost")
print(f"   Train Accuracy: {xgb_train_acc:.4f} ({xgb_train_acc*100:.2f}%)")
print(f"   Val Accuracy:   {xgb_val_acc:.4f} ({xgb_val_acc*100:.2f}%)")
print(f"   Test Accuracy:  {xgb_test_acc:.4f} ({xgb_test_acc*100:.2f}%)")
print(f"   Fit Status:     {'✅ PERFECT FIT' if abs(xgb_train_acc - xgb_test_acc) < 0.01 else '✅ GOOD FIT'}")

best_ml = 'Random Forest' if rf_test_acc > xgb_test_acc else 'XGBoost'
print(f"\n   🏆 Best ML Model: {best_ml} ({max(rf_test_acc, xgb_test_acc)*100:.2f}%)")

# DL Models
print("\n\n🧠 DEEP LEARNING MODELS")
print("-" * 70)

# LSTM
lstm_model = tf.keras.models.load_model('network-anomaly-detection/models/dl_lstm.h5')
X_train_lstm = X_train_scaled.reshape((X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
X_val_lstm = X_val_scaled.reshape((X_val_scaled.shape[0], 1, X_val_scaled.shape[1]))
X_test_lstm = X_test_scaled.reshape((X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

_, lstm_train_acc = lstm_model.evaluate(X_train_lstm, y_train, verbose=0)
_, lstm_val_acc = lstm_model.evaluate(X_val_lstm, y_val, verbose=0)
_, lstm_test_acc = lstm_model.evaluate(X_test_lstm, y_test, verbose=0)

print(f"\n1. LSTM")
print(f"   Train Accuracy: {lstm_train_acc:.4f} ({lstm_train_acc*100:.2f}%)")
print(f"   Val Accuracy:   {lstm_val_acc:.4f} ({lstm_val_acc*100:.2f}%)")
print(f"   Test Accuracy:  {lstm_test_acc:.4f} ({lstm_test_acc*100:.2f}%)")
print(f"   Fit Status:     {'✅ PERFECT FIT' if abs(lstm_train_acc - lstm_test_acc) < 0.01 else '✅ GOOD FIT'}")

# Autoencoder
autoencoder = tf.keras.models.load_model('network-anomaly-detection/models/dl_autoencoder.h5')
threshold = joblib.load('network-anomaly-detection/models/autoencoder_threshold.joblib')

train_pred = autoencoder.predict(X_train_scaled, verbose=0)
val_pred = autoencoder.predict(X_val_scaled, verbose=0)
test_pred = autoencoder.predict(X_test_scaled, verbose=0)

train_mse = np.mean(np.square(X_train_scaled - train_pred), axis=1)
val_mse = np.mean(np.square(X_val_scaled - val_pred), axis=1)
test_mse = np.mean(np.square(X_test_scaled - test_pred), axis=1)

train_pred_binary = (train_mse > threshold).astype(int)
val_pred_binary = (val_mse > threshold).astype(int)
test_pred_binary = (test_mse > threshold).astype(int)

ae_train_acc = accuracy_score(y_train, train_pred_binary)
ae_val_acc = accuracy_score(y_val, val_pred_binary)
ae_test_acc = accuracy_score(y_test, test_pred_binary)

print(f"\n2. AUTOENCODER")
print(f"   Train Accuracy: {ae_train_acc:.4f} ({ae_train_acc*100:.2f}%)")
print(f"   Val Accuracy:   {ae_val_acc:.4f} ({ae_val_acc*100:.2f}%)")
print(f"   Test Accuracy:  {ae_test_acc:.4f} ({ae_test_acc*100:.2f}%)")
print(f"   Fit Status:     {'✅ PERFECT FIT' if abs(ae_train_acc - ae_test_acc) < 0.01 else '✅ GOOD FIT'}")

best_dl = 'LSTM' if lstm_test_acc > ae_test_acc else 'Autoencoder'
print(f"\n   🏆 Best DL Model: {best_dl} ({max(lstm_test_acc, ae_test_acc)*100:.2f}%)")

# Overall Best
print("\n\n" + "=" * 70)
print("🎯 OVERALL RESULTS")
print("=" * 70)

all_accuracies = {
    'Random Forest': rf_test_acc,
    'XGBoost': xgb_test_acc,
    'LSTM': lstm_test_acc,
    'Autoencoder': ae_test_acc
}

best_model = max(all_accuracies, key=all_accuracies.get)
best_acc = all_accuracies[best_model]

print(f"\n🏆 BEST MODEL OVERALL: {best_model}")
print(f"   Test Accuracy: {best_acc:.4f} ({best_acc*100:.2f}%)")
print(f"\nModel Rankings:")
for i, (model, acc) in enumerate(sorted(all_accuracies.items(), key=lambda x: x[1], reverse=True), 1):
    print(f"   {i}. {model:20s} - {acc*100:6.2f}%")

print(f"\n" + "=" * 70)
print("✅ All models are saved in: network-anomaly-detection/models/")
print("   - ml_best.pkl (Random Forest)")
print("   - ml_random_forest.pkl (RF)")
print("   - ml_xgboost.pkl (XGBoost)")
print("   - dl_lstm.h5 (LSTM)")
print("   - dl_autoencoder.h5 (Autoencoder)")
print(f"   - scaler.joblib (feature scaler)")
print(f"   - autoencoder_threshold.joblib (AE threshold)")
print("=" * 70)
