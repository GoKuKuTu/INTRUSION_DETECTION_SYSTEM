#!/usr/bin/env python3
"""
Network Anomaly Detection - Deep Learning Training Pipeline

This script implements deep learning models for network anomaly detection using
TensorFlow/Keras. It supports LSTM, CNN, and Autoencoder architectures with
automatic sequence preparation and comprehensive training callbacks.

Features:
- Multiple DL architectures: LSTM, 1D-CNN, Autoencoder
- Automatic sequence preparation for time-series models
- Comprehensive training callbacks
- Reproducible results with random seeds
- Model persistence in H5 format

Usage:
    python src/train_dl.py --data data/processed/processed.csv --model-type lstm
    python src/train_dl.py --data data/processed/processed.csv --model-type cnn --seq-len 20
    python src/train_dl.py --data data/processed/processed.csv --model-type autoencoder
"""

import argparse
import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import warnings

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dl_training.log')
    ]
)
logger = logging.getLogger(__name__)

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks, optimizers
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
    logger.info("TensorFlow successfully imported")
except Exception as e:
    TENSORFLOW_AVAILABLE = False
    logger.warning(f"TensorFlow not available: {e}")
    logger.warning("Install with: pip install tensorflow")
    # Create dummy classes for type hints when TensorFlow is not available
    class keras:
        class Model:
            pass

# Suppress warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
if TENSORFLOW_AVAILABLE:
    tf.random.set_seed(RANDOM_SEED)


class NetworkAnomalyDLTrainer:
    """
    Deep learning trainer for network anomaly detection.
    
    This class handles sequence preparation, model building, training,
    and evaluation for various deep learning architectures.
    """
    
    def __init__(self, model_type: str, sequence_length: int = 10):
        """
        Initialize the deep learning trainer.
        
        Args:
            model_type (str): Type of model to train ('lstm', 'cnn', 'autoencoder')
            sequence_length (int): Length of sequences for time-series models
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for deep learning training")
        
        self.model_type = model_type.lower()
        self.sequence_length = sequence_length
        self.model = None
        self.history = None
        
        # Validate model type
        valid_types = ['lstm', 'cnn', 'autoencoder']
        if self.model_type not in valid_types:
            raise ValueError(f"Model type must be one of {valid_types}")
        
        logger.info(f"Initialized DL trainer: {self.model_type}, sequence_length: {sequence_length}")
    
    def load_data(self, data_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load processed data and extract features and labels.
        
        Args:
            data_path (str): Path to processed CSV file
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (features, labels)
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
            X = df.drop(columns=['label']).values
            y = df['label'].values
            
            # Convert to binary classification (0: BENIGN, 1: Anomaly)
            # Assuming label 0 is BENIGN, others are anomalies
            y_binary = (y != 0).astype(int)
            
            logger.info(f"Features shape: {X.shape}, Labels shape: {y_binary.shape}")
            logger.info(f"Binary label distribution: {np.bincount(y_binary)}")
            
            return X, y_binary
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def prepare_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert features into sequences for time-series models.
        
        Args:
            X (np.ndarray): Input features
            y (np.ndarray): Target labels
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (sequences, labels)
        """
        if self.model_type not in ['lstm', 'cnn']:
            logger.info("No sequence preparation needed for autoencoder")
            return X, y
        
        logger.info(f"Preparing sequences with length {self.sequence_length}")
        
        # Create sliding window sequences
        sequences = []
        labels = []
        
        for i in range(len(X) - self.sequence_length + 1):
            # Take a window of features
            seq = X[i:i + self.sequence_length]
            # Use the label of the last element in the sequence
            label = y[i + self.sequence_length - 1]
            
            sequences.append(seq)
            labels.append(label)
        
        sequences = np.array(sequences)
        labels = np.array(labels)
        
        logger.info(f"Created sequences: {sequences.shape}")
        logger.info(f"Sequence labels shape: {labels.shape}")
        
        return sequences, labels
    
    def build_lstm_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM model for binary classification.
        
        Args:
            input_shape (Tuple[int, int]): Input shape (sequence_length, n_features)
            
        Returns:
            keras.Model: Compiled LSTM model
        """
        logger.info("Building LSTM model")
        
        model = models.Sequential([
            # First LSTM layer with return sequences for stacked architecture
            layers.LSTM(64, return_sequences=True, input_shape=input_shape),
            layers.Dropout(0.2),  # Dropout for regularization
            
            # Second LSTM layer
            layers.LSTM(32, return_sequences=False),
            layers.Dropout(0.2),
            
            # Dense layers for classification
            layers.Dense(16, activation='relu'),
            layers.Dropout(0.1),
            
            # Output layer for binary classification
            layers.Dense(1, activation='sigmoid')
        ])
        
        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        logger.info("LSTM model built successfully")
        return model
    
    def build_cnn_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build 1D CNN model for sequence classification.
        
        Args:
            input_shape (Tuple[int, int]): Input shape (sequence_length, n_features)
            
        Returns:
            keras.Model: Compiled CNN model
        """
        logger.info("Building 1D CNN model")
        
        model = models.Sequential([
            # First Conv1D layer
            layers.Conv1D(64, kernel_size=3, activation='relu', input_shape=input_shape),
            layers.BatchNormalization(),  # Batch normalization for stability
            layers.MaxPooling1D(pool_size=2),
            layers.Dropout(0.2),
            
            # Second Conv1D layer
            layers.Conv1D(32, kernel_size=3, activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(pool_size=2),
            layers.Dropout(0.2),
            
            # Global max pooling to reduce dimensions
            layers.GlobalMaxPooling1D(),
            
            # Dense layers for classification
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(16, activation='relu'),
            
            # Output layer for binary classification
            layers.Dense(1, activation='sigmoid')
        ])
        
        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        logger.info("CNN model built successfully")
        return model
    
    def build_autoencoder_model(self, input_shape: int) -> keras.Model:
        """
        Build autoencoder model for unsupervised anomaly detection.
        
        Args:
            input_shape (int): Number of input features
            
        Returns:
            keras.Model: Compiled autoencoder model
        """
        logger.info("Building autoencoder model")
        
        # Encoder
        encoder_input = layers.Input(shape=(input_shape,), name='encoder_input')
        encoder = layers.Dense(64, activation='relu')(encoder_input)
        encoder = layers.Dropout(0.2)(encoder)
        encoder = layers.Dense(32, activation='relu')(encoder)
        encoder = layers.Dropout(0.2)(encoder)
        encoder = layers.Dense(16, activation='relu', name='encoder_output')(encoder)
        
        # Decoder
        decoder = layers.Dense(32, activation='relu')(encoder)
        decoder = layers.Dropout(0.2)(decoder)
        decoder = layers.Dense(64, activation='relu')(decoder)
        decoder = layers.Dropout(0.2)(decoder)
        decoder = layers.Dense(input_shape, activation='linear', name='decoder_output')(decoder)
        
        # Create autoencoder model
        autoencoder = models.Model(encoder_input, decoder, name='autoencoder')
        
        # Compile model
        autoencoder.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',  # Mean squared error for reconstruction
            metrics=['mae']  # Mean absolute error
        )
        
        logger.info("Autoencoder model built successfully")
        return autoencoder
    
    def build_model(self, input_shape: Tuple[int, ...]) -> keras.Model:
        """
        Build the specified model type.
        
        Args:
            input_shape (Tuple[int, ...]): Input shape for the model
            
        Returns:
            keras.Model: Compiled model
        """
        if self.model_type == 'lstm':
            return self.build_lstm_model(input_shape)
        elif self.model_type == 'cnn':
            return self.build_cnn_model(input_shape)
        elif self.model_type == 'autoencoder':
            return self.build_autoencoder_model(input_shape[0])
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def get_callbacks(self, model_path: str) -> list:
        """
        Get training callbacks.
        
        Args:
            model_path (str): Path to save the best model
            
        Returns:
            list: List of Keras callbacks
        """
        callbacks_list = [
            # Early stopping to prevent overfitting
            callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            
            # Model checkpoint to save best model
            callbacks.ModelCheckpoint(
                filepath=model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # Reduce learning rate on plateau
            callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        logger.info("Training callbacks configured")
        return callbacks_list
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray, 
                   epochs: int = 10, batch_size: int = 32) -> keras.Model:
        """
        Train the deep learning model.
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training labels
            X_val (np.ndarray): Validation features
            y_val (np.ndarray): Validation labels
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            
        Returns:
            keras.Model: Trained model
        """
        logger.info(f"Training {self.model_type} model for {epochs} epochs")
        
        # Build model
        input_shape = X_train.shape[1:]
        self.model = self.build_model(input_shape)
        
        # Print model summary
        logger.info("Model architecture:")
        self.model.summary()
        
        # Get callbacks
        temp_model_path = f"temp_best_{self.model_type}.h5"
        callbacks_list = self.get_callbacks(temp_model_path)
        
        # Train model
        if self.model_type == 'autoencoder':
            # For autoencoder, use only normal data for training
            normal_mask = y_train == 0
            X_train_normal = X_train[normal_mask]
            logger.info(f"Training autoencoder on {len(X_train_normal)} normal samples")
            
            self.history = self.model.fit(
                X_train_normal, X_train_normal,  # Autoencoder: input = target
                validation_data=(X_val, X_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks_list,
                verbose=1
            )
        else:
            # For supervised models
            self.history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks_list,
                verbose=1
            )
        
        # Load best model
        if Path(temp_model_path).exists():
            self.model = keras.models.load_model(temp_model_path)
            Path(temp_model_path).unlink()  # Remove temporary file
            logger.info("Loaded best model from checkpoint")
        
        logger.info("Model training completed")
        return self.model
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate the trained model.
        
        Args:
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test labels
            
        Returns:
            Dict[str, float]: Evaluation metrics
        """
        logger.info("Evaluating model on test set")
        
        if self.model_type == 'autoencoder':
            # For autoencoder, calculate reconstruction error
            predictions = self.model.predict(X_test)
            mse = np.mean(np.square(X_test - predictions), axis=1)
            
            # Use reconstruction error as anomaly score
            # Higher error = more likely to be anomaly
            threshold = np.percentile(mse, 95)  # 95th percentile as threshold
            y_pred = (mse > threshold).astype(int)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            metrics = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'reconstruction_mse': np.mean(mse)
            }
        else:
            # For supervised models
            predictions = self.model.predict(X_test)
            y_pred = (predictions > 0.5).astype(int).flatten()
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            metrics = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }
        
        logger.info(f"Evaluation metrics: {metrics}")
        return metrics
    
    def save_model(self, output_path: str):
        """
        Save the trained model to disk.
        
        Args:
            output_path (str): Path to save the model
        """
        if self.model is None:
            logger.error("No model to save")
            return
        
        # Create output directory
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        self.model.save(output_path)
        logger.info(f"Model saved to {output_path}")
    
    def print_training_summary(self):
        """Print training history summary."""
        if self.history is None:
            logger.warning("No training history available")
            return
        
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        
        # Get final metrics
        final_loss = self.history.history['loss'][-1]
        final_val_loss = self.history.history['val_loss'][-1]
        
        print(f"Final Training Loss: {final_loss:.4f}")
        print(f"Final Validation Loss: {final_val_loss:.4f}")
        
        # Print best metrics
        best_epoch = np.argmin(self.history.history['val_loss']) + 1
        best_val_loss = min(self.history.history['val_loss'])
        
        print(f"Best Epoch: {best_epoch}")
        print(f"Best Validation Loss: {best_val_loss:.4f}")
        
        print("="*60)
    
    def train_pipeline(self, data_path: str, output_path: str, 
                      epochs: int = 10, batch_size: int = 32) -> Dict[str, Any]:
        """
        Run the complete deep learning training pipeline.
        
        Args:
            data_path (str): Path to processed data
            output_path (str): Path to save trained model
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            
        Returns:
            Dict[str, Any]: Training results
        """
        logger.info("Starting deep learning training pipeline")
        
        # Load data
        X, y = self.load_data(data_path)
        
        # Prepare sequences if needed
        X, y = self.prepare_sequences(X, y)
        
        # Split data (80/20)
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Further split training data for validation (80/20 of training)
        val_split_idx = int(0.8 * len(X_train))
        X_train, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
        y_train, y_val = y_train[:val_split_idx], y_train[val_split_idx:]
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Validation set: {X_val.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        # Train model
        trained_model = self.train_model(X_train, y_train, X_val, y_val, epochs, batch_size)
        
        # Evaluate model
        metrics = self.evaluate_model(X_test, y_test)
        
        # Print training summary
        self.print_training_summary()
        
        # Save model
        self.save_model(output_path)
        
        logger.info("Deep learning training pipeline completed successfully")
        
        return {
            'model': trained_model,
            'metrics': metrics,
            'history': self.history
        }


def main():
    """
    Main function to run the deep learning training pipeline from command line.
    """
    parser = argparse.ArgumentParser(
        description="Network Anomaly Detection - Deep Learning Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/train_dl.py --data data/processed/processed.csv --model-type lstm
  python src/train_dl.py --data data/processed/processed.csv --model-type cnn --seq-len 20
  python src/train_dl.py --data data/processed/processed.csv --model-type autoencoder
  python src/train_dl.py --data data/processed/auto_generated.csv --model-type lstm --out-model models/custom_lstm.h5
        """
    )
    
    parser.add_argument(
        '--data', 
        type=str, 
        default='data/processed/processed.csv',
        help='Path to processed CSV file (default: data/processed/processed.csv)'
    )
    
    parser.add_argument(
        '--model-type', 
        type=str, 
        choices=['lstm', 'cnn', 'autoencoder'],
        default='lstm',
        help='Type of deep learning model to train (default: lstm)'
    )
    
    parser.add_argument(
        '--out-model', 
        type=str, 
        default=None,
        help='Path to save trained model (default: models/dl_{model-type}.h5)'
    )
    
    parser.add_argument(
        '--seq-len', 
        type=int, 
        default=10,
        help='Sequence length for LSTM/CNN models (default: 10)'
    )
    
    parser.add_argument(
        '--epochs', 
        type=int, 
        default=10,
        help='Number of training epochs (default: 10)'
    )
    
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=32,
        help='Batch size for training (default: 32)'
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
    
    # Set default output path if not provided
    if args.out_model is None:
        args.out_model = f"models/dl_{args.model_type}.h5"
    
    try:
        # Initialize trainer
        trainer = NetworkAnomalyDLTrainer(
            model_type=args.model_type,
            sequence_length=args.seq_len
        )
        
        # Run training pipeline
        results = trainer.train_pipeline(
            data_path=args.data,
            output_path=args.out_model,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
        
        # Print summary
        print(f"\n[SUCCESS] Deep learning training completed!")
        print(f"Model type: {args.model_type}")
        print(f"Model saved to: {args.out_model}")
        print(f"Test metrics: {results['metrics']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"[ERROR] Deep learning training failed: {e}")
        return 1


if __name__ == "__main__":
    # Example usage
    print("Network Anomaly Detection - Deep Learning Training Pipeline")
    print("Example usage:")
    print("  python src/train_dl.py --data data/processed/processed.csv --model-type lstm")
    print("  python src/train_dl.py --data data/processed/processed.csv --model-type cnn --seq-len 20")
    print("  python src/train_dl.py --data data/processed/processed.csv --model-type autoencoder")
    print()
    
    exit(main())
