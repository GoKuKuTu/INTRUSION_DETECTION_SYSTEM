#!/usr/bin/env python3
"""
Network Anomaly Detection - Machine Learning Training Pipeline

This script implements a comprehensive machine learning training pipeline for network
anomaly detection. It supports multiple algorithms, handles class imbalance, and
provides detailed evaluation metrics.

Features:
- Multiple ML algorithms: Random Forest, XGBoost, SVM
- Class imbalance handling with SMOTE
- Stratified train/test splitting with optional time-based splitting
- Comprehensive evaluation metrics
- Model persistence and selection
- Quick and full training modes

Usage:
    python src/train_ml.py --data data/processed/processed.csv --out-model models/ml_best.pkl
    python src/train_ml.py --data data/processed/processed.csv --mode quick --time-split
    python src/train_ml.py --data data/processed/processed.csv --mode full
"""

import argparse
import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import joblib
import warnings

# Machine Learning imports
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns

# XGBoost and imbalanced learning
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available. Install with: pip install xgboost")

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    logging.warning("SMOTE not available. Install with: pip install imbalanced-learn")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ml_training.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore')


class NetworkAnomalyTrainer:
    """
    Machine learning trainer for network anomaly detection.
    
    This class handles the complete ML pipeline including data loading,
    preprocessing, model training, evaluation, and persistence.
    """
    
    def __init__(self, mode: str = 'quick', time_split: bool = False):
        """
        Initialize the trainer.
        
        Args:
            mode (str): Training mode - 'quick' for fast training, 'full' for comprehensive
            time_split (bool): Whether to use time-based splitting instead of random
        """
        self.mode = mode
        self.time_split = time_split
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_score = 0
        self.label_encoder = None
        
        logger.info(f"Initialized trainer with mode: {mode}, time_split: {time_split}")
    
    def load_data(self, data_path: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Load processed data and extract features and labels.
        
        Args:
            data_path (str): Path to processed CSV file
            
        Returns:
            Tuple[pd.DataFrame, np.ndarray]: (features, labels)
        """
        logger.info(f"Loading data from {data_path}")
        
        try:
            df = pd.read_csv(data_path)
            logger.info(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Check for label column
            if 'label' not in df.columns:
                logger.error("Label column 'label' not found in data")
                raise ValueError("Label column 'label' is required")
            
            # Separate features and labels
            X = df.drop(columns=['label'])
            y = df['label']
            
            # Handle label encoding if needed
            if y.dtype == 'object':
                self.label_encoder = LabelEncoder()
                y = self.label_encoder.fit_transform(y)
                logger.info(f"Label encoded. Classes: {self.label_encoder.classes_}")
            else:
                logger.info("Labels are already numeric")
            
            logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")
            logger.info(f"Label distribution: {np.bincount(y)}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def check_class_imbalance(self, y: np.ndarray) -> bool:
        """
        Check if class imbalance is severe (> 1:10 ratio).
        
        Args:
            y (np.ndarray): Target labels
            
        Returns:
            bool: True if severe imbalance detected
        """
        class_counts = np.bincount(y)
        max_count = np.max(class_counts)
        min_count = np.min(class_counts)
        
        imbalance_ratio = max_count / min_count
        logger.info(f"Class imbalance ratio: {imbalance_ratio:.2f}")
        
        return imbalance_ratio > 10
    
    def split_data(self, X: pd.DataFrame, y: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Split data into training and testing sets.
        
        Args:
            X (pd.DataFrame): Features
            y (np.ndarray): Labels
            
        Returns:
            Tuple: (X_train, X_test, y_train, y_test)
        """
        logger.info("Splitting data into train/test sets")
        
        if self.time_split:
            # Time-based split (assumes data is ordered by time)
            split_idx = int(0.8 * len(X))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            logger.info("Used time-based splitting")
        else:
            # Stratified random split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            logger.info("Used stratified random splitting")
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        return X_train, X_test, y_train, y_test
    
    def handle_class_imbalance(self, X_train: pd.DataFrame, y_train: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Handle class imbalance using SMOTE if needed.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (np.ndarray): Training labels
            
        Returns:
            Tuple[pd.DataFrame, np.ndarray]: Balanced training data
        """
        if not SMOTE_AVAILABLE:
            logger.warning("SMOTE not available, skipping class balancing")
            return X_train, y_train
        
        # Check if we should apply SMOTE
        should_apply_smote = (
            self.mode == 'full' or 
            self.check_class_imbalance(y_train)
        )
        
        if not should_apply_smote:
            logger.info("Skipping SMOTE (quick mode and no severe imbalance)")
            return X_train, y_train
        
        logger.info("Applying SMOTE for class balancing")
        
        try:
            smote = SMOTE(random_state=42)
            X_balanced, y_balanced = smote.fit_resample(X_train, y_train)
            
            logger.info(f"SMOTE applied. Original: {X_train.shape[0]} samples")
            logger.info(f"Balanced: {X_balanced.shape[0]} samples")
            logger.info(f"New label distribution: {np.bincount(y_balanced)}")
            
            return pd.DataFrame(X_balanced, columns=X_train.columns), y_balanced
            
        except Exception as e:
            logger.warning(f"SMOTE failed: {e}. Using original data.")
            return X_train, y_train
    
    def get_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get model configurations based on training mode.
        
        Returns:
            Dict[str, Dict[str, Any]]: Model configurations
        """
        if self.mode == 'quick':
            # Fast training with minimal hyperparameters
            configs = {
                'RandomForest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': 50,
                        'max_depth': 10,
                        'random_state': 42,
                        'n_jobs': -1
                    }
                },
                'SVM': {
                    'model': SVC,
                    'params': {
                        'kernel': 'rbf',
                        'C': 1.0,
                        'random_state': 42,
                        'probability': True
                    }
                }
            }
            
            if XGBOOST_AVAILABLE:
                configs['XGBoost'] = {
                    'model': xgb.XGBClassifier,
                    'params': {
                        'n_estimators': 50,
                        'max_depth': 6,
                        'random_state': 42,
                        'n_jobs': -1
                    }
                }
        else:
            # Full training with comprehensive hyperparameters
            configs = {
                'RandomForest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': 200,
                        'max_depth': 20,
                        'min_samples_split': 5,
                        'min_samples_leaf': 2,
                        'random_state': 42,
                        'n_jobs': -1
                    }
                },
                'SVM': {
                    'model': SVC,
                    'params': {
                        'kernel': 'rbf',
                        'C': 10.0,
                        'gamma': 'scale',
                        'random_state': 42,
                        'probability': True
                    }
                }
            }
            
            if XGBOOST_AVAILABLE:
                configs['XGBoost'] = {
                    'model': xgb.XGBClassifier,
                    'params': {
                        'n_estimators': 200,
                        'max_depth': 8,
                        'learning_rate': 0.1,
                        'subsample': 0.8,
                        'colsample_bytree': 0.8,
                        'random_state': 42,
                        'n_jobs': -1
                    }
                }
        
        return configs
    
    def train_models(self, X_train: pd.DataFrame, y_train: np.ndarray) -> Dict[str, Any]:
        """
        Train multiple machine learning models.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (np.ndarray): Training labels
            
        Returns:
            Dict[str, Any]: Trained models
        """
        logger.info("Training machine learning models")
        
        configs = self.get_model_configs()
        trained_models = {}
        
        for name, config in configs.items():
            logger.info(f"Training {name}...")
            
            try:
                # Initialize model
                model = config['model'](**config['params'])
                
                # Train model
                model.fit(X_train, y_train)
                trained_models[name] = model
                
                logger.info(f"Successfully trained {name}")
                
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
                continue
        
        self.models = trained_models
        logger.info(f"Trained {len(trained_models)} models successfully")
        
        return trained_models
    
    def evaluate_models(self, X_test: pd.DataFrame, y_test: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Evaluate all trained models on test data.
        
        Args:
            X_test (pd.DataFrame): Test features
            y_test (np.ndarray): Test labels
            
        Returns:
            Dict[str, Dict[str, float]]: Evaluation results
        """
        logger.info("Evaluating models on test set")
        
        results = {}
        
        for name, model in self.models.items():
            logger.info(f"Evaluating {name}...")
            
            try:
                # Make predictions
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                # ROC-AUC (if probabilities available)
                roc_auc = None
                if y_pred_proba is not None:
                    try:
                        roc_auc = roc_auc_score(y_test, y_pred_proba)
                    except ValueError:
                        # Handle case where only one class is present
                        roc_auc = 0.5
                
                # Store results
                results[name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1,
                    'roc_auc': roc_auc,
                    'predictions': y_pred,
                    'probabilities': y_pred_proba
                }
                
                logger.info(f"{name} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate {name}: {e}")
                continue
        
        self.results = results
        return results
    
    def print_evaluation_results(self):
        """Print comprehensive evaluation results."""
        if not self.results:
            logger.warning("No evaluation results available")
            return
        
        print("\n" + "="*80)
        print("MODEL EVALUATION RESULTS")
        print("="*80)
        
        # Print metrics table
        print(f"{'Model':<15} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'ROC-AUC':<10}")
        print("-" * 80)
        
        for name, metrics in self.results.items():
            roc_auc_str = f"{metrics['roc_auc']:.4f}" if metrics['roc_auc'] is not None else "N/A"
            print(f"{name:<15} {metrics['accuracy']:<10.4f} {metrics['precision']:<10.4f} "
                  f"{metrics['recall']:<10.4f} {metrics['f1']:<10.4f} {roc_auc_str:<10}")
        
        # Find and highlight best model
        best_model_name = max(self.results.keys(), key=lambda x: self.results[x]['f1'])
        best_f1 = self.results[best_model_name]['f1']
        
        print("-" * 80)
        print(f"Best Model: {best_model_name} (F1-Score: {best_f1:.4f})")
        print("="*80)
        
        # Print confusion matrix for best model
        if best_model_name in self.results:
            self.plot_confusion_matrix(best_model_name)
    
    def plot_confusion_matrix(self, model_name: str):
        """
        Plot confusion matrix for a specific model.
        
        Args:
            model_name (str): Name of the model
        """
        if model_name not in self.results:
            return
        
        try:
            # Get predictions (assuming we have test data stored)
            # For now, we'll skip the actual plotting but log the matrix
            predictions = self.results[model_name]['predictions']
            
            # This would need access to y_test, so we'll just log the info
            logger.info(f"Confusion matrix for {model_name} would be displayed here")
            
        except Exception as e:
            logger.warning(f"Could not plot confusion matrix for {model_name}: {e}")
    
    def save_best_model(self, output_path: str):
        """
        Save the best performing model to disk.
        
        Args:
            output_path (str): Path to save the model
        """
        if not self.results:
            logger.error("No results available to determine best model")
            return
        
        # Find best model by F1 score
        best_model_name = max(self.results.keys(), key=lambda x: self.results[x]['f1'])
        best_model = self.models[best_model_name]
        best_score = self.results[best_model_name]['f1']
        
        # Create output directory
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump(best_model, output_path)
        
        # Save metadata
        metadata = {
            'model_name': best_model_name,
            'f1_score': best_score,
            'all_results': self.results,
            'label_encoder': self.label_encoder
        }
        
        metadata_path = output_file.parent / f"{output_file.stem}_metadata.joblib"
        joblib.dump(metadata, metadata_path)
        
        self.best_model = best_model
        self.best_score = best_score
        
        logger.info(f"Saved best model ({best_model_name}) to {output_path}")
        logger.info(f"Model F1-Score: {best_score:.4f}")
    
    def train_pipeline(self, data_path: str, output_path: str) -> Dict[str, Any]:
        """
        Run the complete training pipeline.
        
        Args:
            data_path (str): Path to processed data
            output_path (str): Path to save best model
            
        Returns:
            Dict[str, Any]: Training results
        """
        logger.info("Starting ML training pipeline")
        
        # Load data
        X, y = self.load_data(data_path)
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # Handle class imbalance
        X_train_balanced, y_train_balanced = self.handle_class_imbalance(X_train, y_train)
        
        # Train models
        trained_models = self.train_models(X_train_balanced, y_train_balanced)
        
        # Evaluate models
        results = self.evaluate_models(X_test, y_test)
        
        # Print results
        self.print_evaluation_results()
        
        # Save best model
        self.save_best_model(output_path)
        
        logger.info("ML training pipeline completed successfully")
        
        return {
            'models': trained_models,
            'results': results,
            'best_model_name': max(results.keys(), key=lambda x: results[x]['f1']) if results else None,
            'best_f1_score': max(results.values(), key=lambda x: x['f1'])['f1'] if results else 0
        }


def main():
    """
    Main function to run the ML training pipeline from command line.
    """
    parser = argparse.ArgumentParser(
        description="Network Anomaly Detection - Machine Learning Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/train_ml.py --data data/processed/processed.csv --out-model models/ml_best.pkl
  python src/train_ml.py --data data/processed/processed.csv --mode quick --time-split
  python src/train_ml.py --data data/processed/processed.csv --mode full
  python src/train_ml.py --data data/processed/auto_generated.csv --out-model models/quick_model.pkl --mode quick
        """
    )
    
    parser.add_argument(
        '--data', 
        type=str, 
        default='data/processed/processed.csv',
        help='Path to processed CSV file (default: data/processed/processed.csv)'
    )
    
    parser.add_argument(
        '--out-model', 
        type=str, 
        default='models/ml_best.pkl',
        help='Path to save best model (default: models/ml_best.pkl)'
    )
    
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['quick', 'full'],
        default='quick',
        help='Training mode: quick (fast) or full (comprehensive) (default: quick)'
    )
    
    parser.add_argument(
        '--time-split', 
        action='store_true',
        help='Use time-based splitting instead of random stratified split'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize trainer
        trainer = NetworkAnomalyTrainer(
            mode=args.mode,
            time_split=args.time_split
        )
        
        # Run training pipeline
        results = trainer.train_pipeline(
            data_path=args.data,
            output_path=args.out_model
        )
        
        # Print summary
        print(f"\n[SUCCESS] Training completed!")
        print(f"Best model: {results['best_model_name']}")
        print(f"Best F1-Score: {results['best_f1_score']:.4f}")
        print(f"Model saved to: {args.out_model}")
        
        return 0
        
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {e}")
        return 1


if __name__ == "__main__":
    # Example usage
    print("Network Anomaly Detection - ML Training Pipeline")
    print("Example usage:")
    print("  python src/train_ml.py --data data/processed/processed.csv --mode quick")
    print("  python src/train_ml.py --data data/processed/processed.csv --mode full --time-split")
    print()
    
    exit(main())
