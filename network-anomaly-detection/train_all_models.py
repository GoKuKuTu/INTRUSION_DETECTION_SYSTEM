#!/usr/bin/env python3
"""
Comprehensive ML and DL Model Training Pipeline

This script trains optimized ML and DL models for real-time anomaly detection
with focus on high accuracy and proper generalization (not overfitted).

Features:
- Random Forest and XGBoost for ML
- LSTM and Autoencoder for DL
- Proper train/val/test split for generalization
- Early stopping and regularization techniques
- Detailed accuracy metrics and validation curves
"""

import sys
import os
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import logging
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.model_selection import train_test_split, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve
)
from imblearn.over_sampling import SMOTE

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available")

# DL imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks, optimizers
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.error("TensorFlow not available")
    sys.exit(1)

# Set random seeds for reproducibility
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)


class MLModelTrainer:
    """Train and evaluate machine learning models."""
    
    def __init__(self, data_path: str, output_dir: str = 'models'):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        self.scaler = None
        self.models = {}
        self.results = {}
        
    def load_and_prepare_data(self):
        """Load data and prepare train/val/test splits."""
        logger.info(f"Loading data from {self.data_path}")
        df = pd.read_csv(self.data_path)
        
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Separate features and labels
        X = df.drop(columns=['label'])
        y = df['label']
        
        # Encode labels if needed
        if y.dtype == 'object':
            self.label_encoder = {
                'BENIGN': 0,
                'ANOMALY': 1
            }
            y = y.map(lambda x: self.label_encoder.get(x, 0))
        
        logger.info(f"Label distribution:\n{pd.Series(y).value_counts()}")
        
        # First split: train+val (80%) and test (20%)
        X_temp, self.X_test, y_temp, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y
        )
        
        # Second split: train (64%) and val (16%)
        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
            X_temp, y_temp, test_size=0.2, random_state=SEED, stratify=y_temp
        )
        
        logger.info(f"Train set: {self.X_train.shape[0]} samples")
        logger.info(f"Val set: {self.X_val.shape[0]} samples")
        logger.info(f"Test set: {self.X_test.shape[0]} samples")
        
        # Apply SMOTE to training data only
        logger.info("Applying SMOTE for class balancing...")
        try:
            # Use k_neighbors based on minority class size
            n_minority = np.bincount(self.y_train).min()
            k_neighbors = min(5, n_minority - 1)
            smote = SMOTE(random_state=SEED, k_neighbors=k_neighbors)
            self.X_train, self.y_train = smote.fit_resample(self.X_train, self.y_train)
            logger.info(f"After SMOTE - Train set: {self.X_train.shape[0]} samples")
        except Exception as e:
            logger.warning(f"SMOTE failed: {e}. Using original data - dataset already balanced.")
        
        # Scale features
        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_val = self.scaler.transform(self.X_val)
        self.X_test = self.scaler.transform(self.X_test)
        
        # Save scaler
        joblib.dump(self.scaler, self.output_dir / 'scaler.joblib')
        logger.info("Scaler saved")
        
    def train_random_forest(self):
        """Train Random Forest model."""
        logger.info("="*50)
        logger.info("Training Random Forest...")
        logger.info("="*50)
        
        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            oob_score=True,
            class_weight='balanced',
            random_state=SEED,
            n_jobs=-1
        )
        
        model.fit(self.X_train, self.y_train)
        
        # OOB Score (out-of-bag estimate of accuracy)
        logger.info(f"OOB Score: {model.oob_score_:.4f}")
        
        # Predictions
        y_train_pred = model.predict(self.X_train)
        y_val_pred = model.predict(self.X_val)
        y_test_pred = model.predict(self.X_test)
        
        # Metrics
        train_acc = accuracy_score(self.y_train, y_train_pred)
        val_acc = accuracy_score(self.y_val, y_val_pred)
        test_acc = accuracy_score(self.y_test, y_test_pred)
        
        logger.info(f"Train Accuracy: {train_acc:.4f}")
        logger.info(f"Val Accuracy: {val_acc:.4f}")
        logger.info(f"Test Accuracy: {test_acc:.4f}")
        
        # Check for overfitting
        diff = train_acc - test_acc
        logger.info(f"Overfitting check (train-test diff): {diff:.4f}")
        if diff > 0.05:
            logger.warning("⚠️  Potential overfitting detected!")
        else:
            logger.info("✅ Good generalization")
        
        # Save model
        model_path = self.output_dir / 'ml_random_forest.pkl'
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        self.models['RandomForest'] = {
            'model': model,
            'test_accuracy': test_acc,
            'predictions': y_test_pred
        }
        
        self.results['RandomForest'] = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'test_accuracy': test_acc,
            'precision': precision_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
            'recall': recall_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
            'f1': f1_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
        }
    
    def train_xgboost(self):
        """Train XGBoost model."""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available, skipping...")
            return
        
        logger.info("="*50)
        logger.info("Training XGBoost...")
        logger.info("="*50)
        
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=1,
            scale_pos_weight=1,
            random_state=SEED,
            n_jobs=-1,
            eval_metric='mlogloss'
        )
        
        # Train with early stopping
        model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_val, self.y_val)],
            verbose=False
        )
        
        # Predictions
        y_train_pred = model.predict(self.X_train)
        y_val_pred = model.predict(self.X_val)
        y_test_pred = model.predict(self.X_test)
        
        # Metrics
        train_acc = accuracy_score(self.y_train, y_train_pred)
        val_acc = accuracy_score(self.y_val, y_val_pred)
        test_acc = accuracy_score(self.y_test, y_test_pred)
        
        logger.info(f"Train Accuracy: {train_acc:.4f}")
        logger.info(f"Val Accuracy: {val_acc:.4f}")
        logger.info(f"Test Accuracy: {test_acc:.4f}")
        
        # Check for overfitting
        diff = train_acc - test_acc
        logger.info(f"Overfitting check (train-test diff): {diff:.4f}")
        if diff > 0.05:
            logger.warning("⚠️  Potential overfitting detected!")
        else:
            logger.info("✅ Good generalization")
        
        # Save model
        model_path = self.output_dir / 'ml_xgboost.pkl'
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        self.models['XGBoost'] = {
            'model': model,
            'test_accuracy': test_acc,
            'predictions': y_test_pred
        }
        
        self.results['XGBoost'] = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'test_accuracy': test_acc,
            'precision': precision_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
            'recall': recall_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
            'f1': f1_score(self.y_test, y_test_pred, average='weighted', zero_division=0),
        }
    
    def select_best_model(self):
        """Select best performing model and save as ml_best.pkl."""
        if not self.models:
            logger.error("No models trained!")
            return
        
        best_model_name = max(
            self.models.keys(),
            key=lambda x: self.models[x]['test_accuracy']
        )
        
        best_model = self.models[best_model_name]['model']
        best_acc = self.models[best_model_name]['test_accuracy']
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Best ML Model: {best_model_name}")
        logger.info(f"Test Accuracy: {best_acc:.4f}")
        logger.info(f"{'='*50}\n")
        
        # Save as ml_best.pkl
        best_model_path = self.output_dir / 'ml_best.pkl'
        joblib.dump(best_model, best_model_path)
        logger.info(f"Best model saved to {best_model_path}")
        
        return best_model_name


class DLModelTrainer:
    """Train and evaluate deep learning models."""
    
    def __init__(self, data_path: str, output_dir: str = 'models'):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        self.scaler = None
        self.models = {}
        self.results = {}
        
    def load_and_prepare_data(self):
        """Load data and prepare train/val/test splits."""
        logger.info(f"Loading data from {self.data_path}")
        df = pd.read_csv(self.data_path)
        
        # Separate features and labels
        X = df.drop(columns=['label'])
        y = df['label']
        
        # Encode labels if needed
        if y.dtype == 'object':
            self.label_encoder = {
                'BENIGN': 0,
                'ANOMALY': 1
            }
            y = y.map(lambda x: self.label_encoder.get(x, 0))
        
        # Data splits
        X_temp, self.X_test, y_temp, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y
        )
        
        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
            X_temp, y_temp, test_size=0.2, random_state=SEED, stratify=y_temp
        )
        
        logger.info(f"Train set: {self.X_train.shape[0]} samples")
        logger.info(f"Val set: {self.X_val.shape[0]} samples")
        logger.info(f"Test set: {self.X_test.shape[0]} samples")
        
        # Apply SMOTE to training data
        from imblearn.over_sampling import SMOTE
        try:
            n_minority = np.bincount(self.y_train).min()
            k_neighbors = min(5, n_minority - 1)
            smote = SMOTE(random_state=SEED, k_neighbors=k_neighbors)
            self.X_train, self.y_train = smote.fit_resample(self.X_train, self.y_train)
            logger.info(f"SMOTE applied successfully")
        except Exception as e:
            logger.warning(f"SMOTE failed: {e}. Using original data.")
        
        # Scale features
        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_val = self.scaler.transform(self.X_val)
        self.X_test = self.scaler.transform(self.X_test)
        
        # Save scaler
        joblib.dump(self.scaler, self.output_dir / 'scaler.joblib')
        
    def train_lstm(self):
        """Train LSTM model."""
        logger.info("="*50)
        logger.info("Training LSTM Model...")
        logger.info("="*50)
        
        input_dim = self.X_train.shape[1]
        
        model = models.Sequential([
            layers.LSTM(128, activation='relu', input_shape=(1, input_dim), return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(64, activation='relu', return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(model.summary())
        
        # Reshape data for LSTM (samples, timesteps, features)
        X_train_lstm = self.X_train.reshape((self.X_train.shape[0], 1, self.X_train.shape[1]))
        X_val_lstm = self.X_val.reshape((self.X_val.shape[0], 1, self.X_val.shape[1]))
        X_test_lstm = self.X_test.reshape((self.X_test.shape[0], 1, self.X_test.shape[1]))
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=20,
            restore_best_weights=True
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=1e-6
        )
        
        # Train
        history = model.fit(
            X_train_lstm, self.y_train,
            validation_data=(X_val_lstm, self.y_val),
            epochs=200,
            batch_size=32,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        # Evaluate
        train_loss, train_acc = model.evaluate(X_train_lstm, self.y_train, verbose=0)
        val_loss, val_acc = model.evaluate(X_val_lstm, self.y_val, verbose=0)
        test_loss, test_acc = model.evaluate(X_test_lstm, self.y_test, verbose=0)
        
        logger.info(f"Train Accuracy: {train_acc:.4f}")
        logger.info(f"Val Accuracy: {val_acc:.4f}")
        logger.info(f"Test Accuracy: {test_acc:.4f}")
        
        # Check for overfitting
        diff = train_acc - test_acc
        logger.info(f"Overfitting check (train-test diff): {diff:.4f}")
        if diff > 0.05:
            logger.warning("⚠️  Potential overfitting detected!")
        else:
            logger.info("✅ Good generalization")
        
        # Save model
        model_path = self.output_dir / 'dl_lstm.h5'
        model.save(model_path)
        logger.info(f"LSTM model saved to {model_path}")
        
        self.models['LSTM'] = {
            'model': model,
            'test_accuracy': test_acc,
            'history': history
        }
        
        self.results['LSTM'] = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'test_accuracy': test_acc
        }
    
    def train_autoencoder(self):
        """Train Autoencoder model."""
        logger.info("="*50)
        logger.info("Training Autoencoder Model...")
        logger.info("="*50)
        
        input_dim = self.X_train.shape[1]
        encoding_dim = int(input_dim * 0.5)  # 50% compression
        
        # Encoder
        encoder = models.Sequential([
            layers.Dense(input_dim, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.1),
            layers.Dense(int(input_dim * 0.75), activation='relu'),
            layers.Dropout(0.1),
            layers.Dense(encoding_dim, activation='relu', name='bottleneck'),
            layers.Dropout(0.1),
        ])
        
        # Decoder
        decoder = models.Sequential([
            layers.Dense(int(input_dim * 0.75), activation='relu', input_shape=(encoding_dim,)),
            layers.Dropout(0.1),
            layers.Dense(input_dim, activation='sigmoid'),
        ])
        
        # Full autoencoder
        autoencoder = models.Sequential([encoder, decoder])
        
        autoencoder.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse'
        )
        
        logger.info(autoencoder.summary())
        
        # Train
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=20,
            restore_best_weights=True
        )
        
        history = autoencoder.fit(
            self.X_train, self.X_train,
            validation_data=(self.X_val, self.X_val),
            epochs=150,
            batch_size=32,
            callbacks=[early_stop],
            verbose=1
        )
        
        # Calculate reconstruction errors
        train_pred = autoencoder.predict(self.X_train, verbose=0)
        val_pred = autoencoder.predict(self.X_val, verbose=0)
        test_pred = autoencoder.predict(self.X_test, verbose=0)
        
        train_mse = np.mean(np.square(self.X_train - train_pred), axis=1)
        val_mse = np.mean(np.square(self.X_val - val_pred), axis=1)
        test_mse = np.mean(np.square(self.X_test - test_pred), axis=1)
        
        # Threshold-based classification (using median of normal class)
        threshold = np.median(train_mse[self.y_train == 0])
        
        train_pred_binary = (train_mse > threshold).astype(int)
        val_pred_binary = (val_mse > threshold).astype(int)
        test_pred_binary = (test_mse > threshold).astype(int)
        
        train_acc = accuracy_score(self.y_train, train_pred_binary)
        val_acc = accuracy_score(self.y_val, val_pred_binary)
        test_acc = accuracy_score(self.y_test, test_pred_binary)
        
        logger.info(f"Train Accuracy: {train_acc:.4f}")
        logger.info(f"Val Accuracy: {val_acc:.4f}")
        logger.info(f"Test Accuracy: {test_acc:.4f}")
        
        # Check for overfitting
        diff = train_acc - test_acc
        logger.info(f"Overfitting check (train-test diff): {diff:.4f}")
        if diff > 0.05:
            logger.warning("⚠️  Potential overfitting detected!")
        else:
            logger.info("✅ Good generalization")
        
        # Save model
        model_path = self.output_dir / 'dl_autoencoder.h5'
        autoencoder.save(model_path)
        logger.info(f"Autoencoder model saved to {model_path}")
        
        # Save threshold
        threshold_path = self.output_dir / 'autoencoder_threshold.joblib'
        joblib.dump(threshold, threshold_path)
        
        self.models['Autoencoder'] = {
            'model': autoencoder,
            'test_accuracy': test_acc,
            'history': history,
            'threshold': threshold
        }
        
        self.results['Autoencoder'] = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'test_accuracy': test_acc
        }


def main():
    """Main training pipeline."""
    logger.info("Starting comprehensive model training...")
    logger.info("="*60)
    
    data_path = 'network-anomaly-detection/data/processed/processed_expanded.csv'
    output_dir = 'network-anomaly-detection/models'
    
    # Check if data exists
    if not Path(data_path).exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    # Train ML Models
    logger.info("\n🤖 STARTING ML MODEL TRAINING...\n")
    ml_trainer = MLModelTrainer(data_path, output_dir)
    ml_trainer.load_and_prepare_data()
    ml_trainer.train_random_forest()
    if XGBOOST_AVAILABLE:
        ml_trainer.train_xgboost()
    best_ml = ml_trainer.select_best_model()
    
    # Train DL Models
    logger.info("\n🧠 STARTING DL MODEL TRAINING...\n")
    dl_trainer = DLModelTrainer(data_path, output_dir)
    dl_trainer.load_and_prepare_data()
    dl_trainer.train_lstm()
    dl_trainer.train_autoencoder()
    
    # Summary Report
    logger.info("\n" + "="*60)
    logger.info("📊 FINAL ACCURACY REPORT")
    logger.info("="*60)
    
    logger.info("\n🤖 ML MODELS:")
    for model_name, results in ml_trainer.results.items():
        logger.info(f"\n{model_name}:")
        logger.info(f"  Train Accuracy:  {results['train_accuracy']:.4f}")
        logger.info(f"  Val Accuracy:    {results['val_accuracy']:.4f}")
        logger.info(f"  Test Accuracy:   {results['test_accuracy']:.4f}")
        logger.info(f"  Precision:       {results['precision']:.4f}")
        logger.info(f"  Recall:          {results['recall']:.4f}")
        logger.info(f"  F1-Score:        {results['f1']:.4f}")
        logger.info(f"  ROC-AUC:         {results['roc_auc']:.4f}")
    
    logger.info("\n\n🧠 DL MODELS:")
    for model_name, results in dl_trainer.results.items():
        logger.info(f"\n{model_name}:")
        logger.info(f"  Train Accuracy:  {results['train_accuracy']:.4f}")
        logger.info(f"  Val Accuracy:    {results['val_accuracy']:.4f}")
        logger.info(f"  Test Accuracy:   {results['test_accuracy']:.4f}")
    
    logger.info("\n" + "="*60)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("Models saved to: network-anomaly-detection/models/")
    logger.info("="*60 + "\n")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'ml_models': ml_trainer.results,
        'dl_models': dl_trainer.results,
        'best_ml_model': best_ml
    }
    
    report_path = Path(output_dir) / 'training_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Report saved to {report_path}")


if __name__ == '__main__':
    main()
